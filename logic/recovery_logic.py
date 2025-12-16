"""Recovery (involuntary) contract business logic.

Recovery contracts are for involuntary tows (repos, abandonments, etc.).
- Follows Florida Statute 713.78
- Strict lien timeline: 7 days notice, 35-50 days to sale
- Sale eligibility depends on vehicle age
- Admin/lien fee cap of $250

⚠️ WARNING: This module requires a valid Florida wrecker license.
Set ENABLE_INVOLUNTARY_TOWS = True in config.py only if properly licensed.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Tuple

from models.lot_models import StorageContract, DATE_FORMAT
from utils.config import ENABLE_INVOLUNTARY_TOWS, MAX_ADMIN_FEE, MAX_LIEN_FEE

# Florida Statute 713.78 timeline
RECOVERY_SCHEDULE = {
    "lien_notice_deadline_days": 7,     # Must send lien notice within 7 business days
    "sale_wait_days_new_vehicle": 50,   # Vehicles < 3 years old
    "sale_wait_days_old_vehicle": 35,   # Vehicles >= 3 years old
    "min_notice_to_sale_days": 30,      # Minimum days between notice and sale
    "vehicle_age_threshold": 3,         # Age threshold for old vs new
}


def calculate_recovery_fees(contract: StorageContract) -> float:
    """Calculate recovery fees for involuntary recovery contract.
    
    ⚠️ WARNING: Requires Florida wrecker license. Returns 0.0 if not enabled.
    
    Includes:
    - Recovery handling fee (initial)
    - Lien processing fee (if lien filed)
    - Certified mail fees
    - Title search, DMV, sale fees
    
    Args:
        contract: Recovery contract
        
    Returns:
        Total recovery fees in dollars
    """
    if not ENABLE_INVOLUNTARY_TOWS:
        return 0.0
    
    total = 0.0
    
    # Recovery handling fee
    total += contract.recovery_handling_fee
    
    # Lien processing fee (only if lien process started)
    if contract.notices_sent > 0:
        total += contract.lien_processing_fee
    
    # Certified mail (first notice)
    if contract.notices_sent >= 1:
        total += contract.cert_mail_fee
    
    # Second certified mail (if second notice sent)
    if contract.notices_sent >= 2:
        total += contract.cert_mail_fee
    
    # Title search, DMV, and sale fees (if applicable)
    # These are typically added when lien is processed
    if contract.notices_sent > 0:
        total += contract.title_search_fee
        total += contract.dmv_fee
    
    return total


def calculate_recovery_storage_fees(contract: StorageContract, as_of_date: datetime = None) -> float:
    """Calculate storage fees for recovery contract.
    
    Storage fees apply from day one of recovery.
    
    Args:
        contract: Recovery contract with storage rates
        as_of_date: Date to calculate through (default: today)
        
    Returns:
        Total storage fees in dollars
    """
    from . import storage_logic
    
    # Delegate to storage logic
    return storage_logic.calculate_storage_fees(contract, as_of_date)


def recovery_lien_timeline(contract: StorageContract) -> dict:
    """Calculate lien timeline for recovery contract per FL Statute 713.78.
    
    Timeline depends on vehicle age:
    - New vehicles (<3 years): 50 days from recovery to sale
    - Old vehicles (≥3 years): 35 days from recovery to sale
    - Must send lien notice within 7 days
    
    Args:
        contract: Recovery contract
        
    Returns:
        Dictionary with timeline dates and eligibility flags
    """
    start = datetime.strptime(contract.start_date, DATE_FORMAT)
    
    # Determine vehicle age
    current_year = datetime.now().year
    vehicle_age = current_year - (contract.vehicle.year or current_year)
    is_new_vehicle = vehicle_age < RECOVERY_SCHEDULE["vehicle_age_threshold"]
    
    # Lien notice must be sent within 7 days
    lien_notice_deadline = start + timedelta(days=RECOVERY_SCHEDULE["lien_notice_deadline_days"])
    
    # Sale eligibility depends on vehicle age
    if is_new_vehicle:
        sale_wait_days = RECOVERY_SCHEDULE["sale_wait_days_new_vehicle"]
    else:
        sale_wait_days = RECOVERY_SCHEDULE["sale_wait_days_old_vehicle"]
    
    sale_eligible_date = start + timedelta(days=sale_wait_days)
    
    today = datetime.now()
    
    return {
        "vehicle_age": vehicle_age,
        "is_new_vehicle": is_new_vehicle,
        "lien_notice_deadline": lien_notice_deadline.strftime(DATE_FORMAT),
        "sale_eligible_date": sale_eligible_date.strftime(DATE_FORMAT),
        "is_lien_notice_overdue": today > lien_notice_deadline and contract.notices_sent == 0,
        "is_sale_eligible": today >= sale_eligible_date,
        "days_until_sale": (sale_eligible_date - today).days if today < sale_eligible_date else 0,
        "sale_wait_days": sale_wait_days,
        "statute": "FL 713.78",
    }


def recovery_past_due_status(contract: StorageContract) -> Tuple[bool, int]:
    """Check if recovery contract is past due.
    
    Recovery contracts accrue fees immediately. Since they're involuntary,
    "past due" is more about lien timeline than payment expectation.
    
    Args:
        contract: Recovery contract
        
    Returns:
        Tuple of (is_past_due, days_since_recovery)
    """
    start = datetime.strptime(contract.start_date, DATE_FORMAT)
    days = (datetime.now() - start).days
    
    # Consider past due if no payment and lien notice deadline passed
    from . import lot_logic  # Avoid circular import
    bal = lot_logic.balance(contract)
    
    if bal > 0 and days >= 7:  # After lien notice deadline
        return True, days
    
    return False, 0


def validate_recovery_contract(contract: StorageContract) -> list[str]:
    """Validate recovery contract for FL 713.78 compliance.
    
    Args:
        contract: Recovery contract to validate
        
    Returns:
        List of warning/error messages (empty if valid)
    """
    warnings = []
    
    # Check recovery fees are set
    if contract.recovery_handling_fee <= 0:
        warnings.append("Recovery handling fee must be greater than 0")
    
    # Check storage fees
    if contract.daily_storage_fee <= 0:
        warnings.append("Daily storage fee must be set")
    
    if contract.rate_mode not in ["daily", "weekly", "monthly"]:
        warnings.append("Rate mode must be daily, weekly, or monthly")
    
    # CRITICAL: Check admin/lien fee cap ($250 in FL)
    total_admin_lien = contract.admin_fee + contract.lien_processing_fee
    if total_admin_lien > 250:
        warnings.append(
            f"❌ COMPLIANCE VIOLATION: Admin + Lien fees (${total_admin_lien:.2f}) "
            f"exceed FL cap of $250.00"
        )
    
    # Warn if lien processing fee alone exceeds cap
    if contract.lien_processing_fee > 250:
        warnings.append(f"❌ Lien processing fee ${contract.lien_processing_fee:.2f} exceeds FL cap of $250")
    
    if contract.admin_fee > 250:
        warnings.append(f"⚠ Admin fee ${contract.admin_fee:.2f} exceeds FL cap of $250")
    
    # Check required fees are set
    if contract.cert_mail_fee <= 0:
        warnings.append("Certified mail fee must be set for lien notices")
    
    # Recovery shouldn't have voluntary tow fees
    if contract.tow_base_fee > 0:
        warnings.append("Recovery contract should use recovery_handling_fee, not tow_base_fee")
    
    # Check vehicle year for age calculation
    if not contract.vehicle.year or contract.vehicle.year < 1900:
        warnings.append("Vehicle year required for proper sale timeline calculation")
    
    # Warn if lien notice overdue
    timeline = recovery_lien_timeline(contract)
    if timeline.get("is_lien_notice_overdue"):
        warnings.append(
            f"⚠ Lien notice OVERDUE - must be sent within 7 days per FL 713.78 "
            f"(deadline: {timeline['lien_notice_deadline']})"
        )
    
    return warnings


def check_sale_eligibility(contract: StorageContract) -> Tuple[bool, str]:
    """Check if recovery contract is eligible for sale.
    
    Sale eligibility requires:
    1. Proper timeline elapsed (35 or 50 days based on vehicle age)
    2. Lien notice sent
    3. FL 713.78 compliance
    
    Args:
        contract: Recovery contract
        
    Returns:
        Tuple of (is_eligible, reason)
    """
    timeline = recovery_lien_timeline(contract)
    
    # Check timeline
    if not timeline["is_sale_eligible"]:
        days_left = timeline["days_until_sale"]
        return False, f"Sale in {days_left} days ({timeline['sale_eligible_date']})"
    
    # Check lien notice sent
    if contract.notices_sent == 0:
        return False, "Lien notice must be sent before sale"
    
    # Check compliance
    warnings = validate_recovery_contract(contract)
    critical_warnings = [w for w in warnings if "❌" in w]
    if critical_warnings:
        return False, f"Compliance issues: {'; '.join(critical_warnings)}"
    
    return True, "Eligible for sale per FL 713.78"
