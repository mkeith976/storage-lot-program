"""Storage-only contract business logic.

Storage contracts are for customers who voluntarily store vehicles.
- No involuntary towing or recovery
- Slower lien timeline than tow/recovery (30/60/90/120 days)
- Lien/sale only if customer doesn't pay
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Tuple

from models.lot_models import StorageContract, DATE_FORMAT

# Storage-only lien schedule (slower than recovery)
STORAGE_SCHEDULE = {
    "first_notice_days": 30,      # First notice eligibility
    "second_notice_days": 60,     # Second notice eligibility  
    "lien_eligible_days": 90,     # Lien eligibility
    "sale_eligible_days": 120,    # Sale eligibility
}


def calculate_storage_fees(contract: StorageContract, as_of_date: datetime = None) -> float:
    """Calculate storage fees for storage-only contract.
    
    Uses explicit daily/weekly/monthly rates from contract.
    Weekly/monthly are independent values, not linear multiples.
    
    Args:
        contract: Storage contract with rate_mode and storage fees
        as_of_date: Date to calculate through (default: today)
        
    Returns:
        Total storage fees in dollars
    """
    if as_of_date is None:
        as_of_date = datetime.now()
    
    start = datetime.strptime(contract.start_date, DATE_FORMAT)
    days = (as_of_date - start).days
    
    if days < 0:
        return 0.0
    
    if contract.rate_mode == "daily":
        return days * contract.daily_storage_fee
    
    elif contract.rate_mode == "weekly":
        weeks = math.ceil(days / 7)
        return weeks * contract.weekly_storage_fee
    
    elif contract.rate_mode == "monthly":
        months = math.ceil(days / 30)
        return months * contract.monthly_storage_fee
    
    else:
        # Fallback to daily if unknown mode
        return days * contract.daily_storage_fee


def storage_lien_timeline(contract: StorageContract) -> dict:
    """Calculate lien timeline for storage-only contract.
    
    Storage uses slower schedule: 30/60/90/120 days.
    No sale eligibility without unpaid storage.
    
    Args:
        contract: Storage contract
        
    Returns:
        Dictionary with timeline dates and eligibility flags
    """
    start = datetime.strptime(contract.start_date, DATE_FORMAT)
    
    first_notice_date = start + timedelta(days=STORAGE_SCHEDULE["first_notice_days"])
    second_notice_date = start + timedelta(days=STORAGE_SCHEDULE["second_notice_days"])
    lien_date = start + timedelta(days=STORAGE_SCHEDULE["lien_eligible_days"])
    sale_date = start + timedelta(days=STORAGE_SCHEDULE["sale_eligible_days"])
    
    today = datetime.now()
    
    return {
        "first_notice_date": first_notice_date.strftime(DATE_FORMAT),
        "second_notice_date": second_notice_date.strftime(DATE_FORMAT),
        "lien_eligible_date": lien_date.strftime(DATE_FORMAT),
        "sale_eligible_date": sale_date.strftime(DATE_FORMAT),
        "is_first_notice_eligible": today >= first_notice_date,
        "is_second_notice_eligible": today >= second_notice_date,
        "is_lien_eligible": today >= lien_date,
        "is_sale_eligible": today >= sale_date,
        "days_until_first_notice": (first_notice_date - today).days if today < first_notice_date else 0,
        "days_until_lien": (lien_date - today).days if today < lien_date else 0,
        "days_until_sale": (sale_date - today).days if today < sale_date else 0,
    }


def storage_past_due_status(contract: StorageContract) -> Tuple[bool, int]:
    """Check if storage contract is past due (has unpaid balance).
    
    Storage contracts are past due if they have any unpaid balance.
    
    Args:
        contract: Storage contract
        
    Returns:
        Tuple of (is_past_due, days_past_due)
    """
    from . import lot_logic  # Avoid circular import
    
    bal = lot_logic.balance(contract)
    
    if bal <= 0:
        return False, 0
    
    # Calculate days since start
    start = datetime.strptime(contract.start_date, DATE_FORMAT)
    days = (datetime.now() - start).days
    
    # Consider past due if unpaid and more than 30 days
    if days >= 30:
        return True, days - 30
    
    return False, 0


def validate_storage_contract(contract: StorageContract) -> list[str]:
    """Validate storage contract for compliance.
    
    Args:
        contract: Storage contract to validate
        
    Returns:
        List of warning/error messages (empty if valid)
    """
    warnings = []
    
    # Check rate mode is set
    if contract.rate_mode not in ["daily", "weekly", "monthly"]:
        warnings.append("Rate mode must be daily, weekly, or monthly")
    
    # Check storage fees are positive
    if contract.daily_storage_fee <= 0:
        warnings.append("Daily storage fee must be greater than 0")
    if contract.weekly_storage_fee <= 0:
        warnings.append("Weekly storage fee must be greater than 0")
    if contract.monthly_storage_fee <= 0:
        warnings.append("Monthly storage fee must be greater than 0")
    
    # Warn if admin fee exceeds $250 (FL cap)
    if contract.admin_fee > 250:
        warnings.append(f"⚠ Admin fee ${contract.admin_fee:.2f} exceeds FL cap of $250")
    
    # Storage-only shouldn't have tow/recovery fees
    if contract.tow_base_fee > 0 or contract.recovery_handling_fee > 0:
        warnings.append("Storage-only contract should not have tow/recovery fees")
    
    return warnings
