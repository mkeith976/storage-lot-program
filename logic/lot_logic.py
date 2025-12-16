"""Business logic for contract calculations and status checks.

NOTE: File I/O operations have been moved to persistence.py module.
This module now contains only business logic and calculation rules.

BUSINESS MODE: This application enforces voluntary-only operations by default.
Recovery/involuntary towing requires proper licensing (see config.py).
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from models.lot_models import (
    DATE_FORMAT,
    Customer,
    Fee,
    Notice,
    Payment,
    StorageContract,
    StorageData,
    Vehicle,
)
from utils.persistence import load_data, save_data, load_fee_templates, save_fee_templates
from utils.config import ENABLE_INVOLUNTARY_TOWS, MAX_ADMIN_FEE, MAX_LIEN_FEE


def add_audit_entry(contract: StorageContract, action: str, details: str = "") -> None:
    """Add timestamped audit log entry to contract.
    
    Creates immutable history of important events for evidence/dispute resolution.
    
    Args:
        contract: Contract to add entry to
        action: Action type (e.g., "Contract Created", "Notice Sent", "Payment Received")
        details: Additional details about the action
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {action}"
    if details:
        entry += f" - {details}"
    contract.audit_log.append(entry)

# Configurable lien schedules by contract type
# Tow & Recovery follows Florida Statute 713.78
TOW_RECOVERY_SCHEDULE = {
    "lien_notice_deadline_days": 7,  # Must send lien notice within 7 business days
    "sale_wait_days_new_vehicle": 50,  # Vehicles < 3 years old
    "sale_wait_days_old_vehicle": 35,  # Vehicles >= 3 years old
    "min_notice_to_sale_days": 30,  # Minimum days between notice and sale
    "vehicle_age_threshold": 3,  # Age threshold for old vs new
}

# Storage Only uses slower schedule (configurable - pending legal review)
STORAGE_ONLY_SCHEDULE = {
    "first_notice_days": 30,  # First notice eligibility
    "second_notice_days": 60,  # Second notice eligibility
    "lien_eligible_days": 90,  # Lien eligibility (later than T&R)
    "sale_eligible_days": 120,  # Sale eligibility (later than T&R)
}

LABOR_BLOCK_MINUTES = 15

DEFAULT_VEHICLE_FEES: Dict[str, Dict[str, float]] = {
    "Car": {
        # Storage fees (all contract types)
        "daily_storage_fee": 35.00,
        "weekly_storage_fee": 210.00,
        "monthly_storage_fee": 840.00,
        
        # Tow contract fees (voluntary)
        "tow_base_fee": 125.00,
        "tow_mileage_rate": 4.00,
        "tow_hourly_labor_rate": 90.00,
        "after_hours_fee": 50.00,
        
        # Recovery contract fees (involuntary)
        "recovery_handling_fee": 125.00,
        "lien_processing_fee": 250.00,
        "cert_mail_fee": 10.00,
        "title_search_fee": 25.00,
        "dmv_fee": 20.00,
        "sale_fee": 100.00,
        
        # Common fees
        "admin_fee": 75.00,
        "labor_rate": 90.00,
    },
    "Truck": {
        "daily_storage_fee": 35.00,
        "weekly_storage_fee": 210.00,
        "monthly_storage_fee": 840.00,
        "tow_base_fee": 150.00,
        "tow_mileage_rate": 4.50,
        "tow_hourly_labor_rate": 90.00,
        "after_hours_fee": 50.00,
        "recovery_handling_fee": 150.00,
        "lien_processing_fee": 250.00,
        "cert_mail_fee": 10.00,
        "title_search_fee": 25.00,
        "dmv_fee": 20.00,
        "sale_fee": 100.00,
        "admin_fee": 75.00,
        "labor_rate": 90.00,
    },
    "Motorcycle": {
        "daily_storage_fee": 20.00,
        "weekly_storage_fee": 120.00,
        "monthly_storage_fee": 480.00,
        "tow_base_fee": 75.00,
        "tow_mileage_rate": 3.00,
        "tow_hourly_labor_rate": 90.00,
        "after_hours_fee": 35.00,
        "recovery_handling_fee": 75.00,
        "lien_processing_fee": 250.00,
        "cert_mail_fee": 10.00,
        "title_search_fee": 25.00,
        "dmv_fee": 20.00,
        "sale_fee": 100.00,
        "admin_fee": 50.00,
        "labor_rate": 90.00,
    },
    "RV": {
        "daily_storage_fee": 45.00,
        "weekly_storage_fee": 270.00,
        "monthly_storage_fee": 1080.00,
        "tow_base_fee": 200.00,
        "tow_mileage_rate": 5.00,
        "tow_hourly_labor_rate": 90.00,
        "after_hours_fee": 75.00,
        "recovery_handling_fee": 200.00,
        "lien_processing_fee": 250.00,
        "cert_mail_fee": 10.00,
        "title_search_fee": 25.00,
        "dmv_fee": 20.00,
        "sale_fee": 100.00,
        "admin_fee": 100.00,
        "labor_rate": 90.00,
    },
    "Boat": {
        "daily_storage_fee": 40.00,
        "weekly_storage_fee": 240.00,
        "monthly_storage_fee": 960.00,
        "tow_base_fee": 175.00,
        "tow_mileage_rate": 4.50,
        "tow_hourly_labor_rate": 90.00,
        "after_hours_fee": 60.00,
        "recovery_handling_fee": 175.00,
        "lien_processing_fee": 250.00,
        "cert_mail_fee": 10.00,
        "title_search_fee": 25.00,
        "dmv_fee": 20.00,
        "sale_fee": 100.00,
        "admin_fee": 85.00,
        "labor_rate": 90.00,
    },
    "Trailer": {
        "daily_storage_fee": 25.00,
        "weekly_storage_fee": 150.00,
        "monthly_storage_fee": 600.00,
        "tow_base_fee": 100.00,
        "tow_mileage_rate": 3.50,
        "tow_hourly_labor_rate": 90.00,
        "after_hours_fee": 40.00,
        "recovery_handling_fee": 100.00,
        "lien_processing_fee": 250.00,
        "cert_mail_fee": 10.00,
        "title_search_fee": 25.00,
        "dmv_fee": 20.00,
        "sale_fee": 100.00,
        "admin_fee": 60.00,
        "labor_rate": 90.00,
    },
}
FEE_TEMPLATES: Dict[str, Dict[str, float]] = {}


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

# Load fee templates at module level for backward compatibility
# NOTE: load_fee_templates and save_fee_templates are imported from persistence.py
FEE_TEMPLATES = load_fee_templates()

# Import specialized logic modules (relative imports within same package)
from . import storage_logic
from . import tow_logic
from . import recovery_logic


# ---------------------------------------------------------------------------
# Fee helpers
# ---------------------------------------------------------------------------

def default_fee_schedule(vehicle_type: str) -> Dict[str, float]:
    return FEE_TEMPLATES.get(vehicle_type, FEE_TEMPLATES.get("Car", DEFAULT_VEHICLE_FEES["Car"]))


def build_contract(
    storage_data: StorageData,
    customer: Customer,
    vehicle: Vehicle,
    start_date: str,
    contract_type: str,
    daily_rate: float,
    tow_fee: float,
    impound_fee: float,
    admin_fee: float,
    tow_base_fee: float,
    mileage_included: float,
    mileage_rate: float,
    certified_mail_fee_first: float,
    certified_mail_fee_second: float,
    extra_labor_minutes: float,
    labor_rate_per_hour: float,
    recovery_miles: float,
) -> StorageContract:
    contract = StorageContract(
        contract_id=storage_data.next_id,
        customer=customer,
        vehicle=vehicle,
        start_date=start_date,
        contract_type=contract_type,
        daily_rate=daily_rate,
        tow_fee=tow_fee,
        impound_fee=impound_fee,
        admin_fee=admin_fee,
        tow_base_fee=tow_base_fee,
        mileage_included=mileage_included,
        mileage_rate=mileage_rate,
        certified_mail_fee_first=certified_mail_fee_first,
        certified_mail_fee_second=certified_mail_fee_second,
        extra_labor_minutes=extra_labor_minutes,
        labor_rate_per_hour=labor_rate_per_hour,
        recovery_miles=recovery_miles,
        lien_eligible_date=(parse_date(start_date) + timedelta(days=LIEN_NOTICE_DAYS + LIEN_BUFFER_DAYS)).strftime(
            DATE_FORMAT
        ),
    )
    contract.fees = [
        Fee("Storage", daily_rate, category="storage", is_default=True),
        Fee("Tow/Impound", tow_fee + impound_fee, category="impound", is_default=True),
        Fee("Admin", admin_fee, category="admin", is_default=True),
        Fee("Tow Base", tow_base_fee, category="recovery", is_default=True),
        Fee("Certified Mail 1st", certified_mail_fee_first, category="recovery", is_default=True),
        Fee("Certified Mail 2nd", certified_mail_fee_second, category="recovery", is_default=True),
    ]
    storage_data.contracts.append(contract)
    storage_data.next_id += 1
    return contract


# ---------------------------------------------------------------------------
# Calculation helpers
# ---------------------------------------------------------------------------

def parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, DATE_FORMAT)


def is_recovery_type(contract: StorageContract) -> bool:
    """Check if contract is recovery/tow & recovery type (subject to FL 713.78 rules).
    
    NOTE: Recovery contracts require proper wrecker licensing.
    This function returns False if ENABLE_INVOLUNTARY_TOWS is disabled,
    preventing recovery contract processing even if legacy data exists.
    """
    if not ENABLE_INVOLUNTARY_TOWS:
        return False
    
    ct = contract.contract_type.lower()
    return ct in ("recovery", "tow & recovery", "tow&recovery")


def is_tow_type(contract: StorageContract) -> bool:
    """Check if contract is voluntary tow type."""
    ct = contract.contract_type.lower()
    return ct == "tow"


def is_storage_type(contract: StorageContract) -> bool:
    """Check if contract is storage only type."""
    ct = contract.contract_type.lower()
    return ct in ("storage", "storage only", "storageonly")


def storage_days(contract: StorageContract, as_of: datetime | None = None) -> int:
    as_of = as_of or datetime.today()
    start = parse_date(contract.start_date)
    delta = as_of.date() - start.date()
    return max(delta.days, 0) + 1


def labor_fee(contract: StorageContract) -> float:
    if contract.extra_labor_minutes <= 0 or contract.labor_rate_per_hour <= 0:
        return 0.0
    blocks = (contract.extra_labor_minutes + LABOR_BLOCK_MINUTES - 1) // LABOR_BLOCK_MINUTES
    hourly_blocks = contract.labor_rate_per_hour / 60
    return round(blocks * LABOR_BLOCK_MINUTES * hourly_blocks, 2)


def recovery_mileage_fee(contract: StorageContract) -> float:
    if contract.mileage_rate <= 0:
        return 0.0
    miles_over = max(0.0, contract.recovery_miles - contract.mileage_included)
    return round(miles_over * contract.mileage_rate, 2)


def calculate_charges(contract: StorageContract, as_of: datetime | None = None) -> Dict[str, float]:
    """
    Calculate charges based on contract type: storage, tow, or recovery.
    
    Delegates to specialized modules for each contract type.
    Enforces Florida fee caps (admin: $250, lien: $250).
    """
    as_of = as_of or datetime.today()
    contract_type = contract.contract_type.lower()
    
    result = {
        "storage": 0.0,
        "tow_impound": 0.0,
        "admin": 0.0,
        "labor": 0.0,
        "recovery": 0.0,
        "tow_fees": 0.0,
        "recovery_fees": 0.0,
    }
    
    # Calculate storage fees (all contract types have storage)
    if contract_type == "tow":
        storage_charge = tow_logic.calculate_tow_storage_fees(contract, as_of)
    elif contract_type == "recovery" and ENABLE_INVOLUNTARY_TOWS:
        storage_charge = recovery_logic.calculate_recovery_storage_fees(contract, as_of)
    else:  # storage only (or recovery when disabled)
        storage_charge = storage_logic.calculate_storage_fees(contract, as_of)
    
    result["storage"] = round(storage_charge, 2)
    
    # Add contract-specific fees
    if contract_type == "tow":
        tow_fees = tow_logic.calculate_tow_fees(contract)
        result["tow_fees"] = round(tow_fees, 2)
        result["admin"] = round(min(contract.admin_fee, MAX_ADMIN_FEE), 2)
        
    elif contract_type == "recovery" and ENABLE_INVOLUNTARY_TOWS:
        recovery_fees = recovery_logic.calculate_recovery_fees(contract)
        result["recovery_fees"] = round(recovery_fees, 2)
        result["recovery"] = result["recovery_fees"]  # Backward compatibility
        result["admin"] = round(min(contract.admin_fee, MAX_ADMIN_FEE), 2)
        
    else:  # storage only (or recovery when disabled, treated as storage)
        result["admin"] = round(min(contract.admin_fee, MAX_ADMIN_FEE), 2)
    
    result["subtotal"] = round(sum(result.values()), 2)
    return result


def total_payments(contract: StorageContract) -> float:
    # Support payments stored as objects with .amount or as dicts with ['amount']
    total = 0.0
    for p in contract.payments:
        if isinstance(p, dict):
            amt = p.get("amount", 0.0)
        else:
            amt = getattr(p, "amount", 0.0)
        try:
            total += float(amt)
        except Exception:
            continue
    return round(total, 2)


def storage_days_breakdown(contract: StorageContract, as_of: datetime | None = None) -> Dict[str, any]:
    """
    Analyze storage days and their collectibility based on lien timing rules.
    
    Returns dict with:
    - total_days: Total storage days charged
    - billable_days: Days clearly collectible (notice sent on time)
    - questionable_days: Days that may not be collectible due to late/missing notice
    - warning: String message if there are collectibility concerns
    - details: Human-readable explanation
    """
    as_of = as_of or datetime.today()
    start = parse_date(contract.start_date)
    total_days = storage_days(contract, as_of)
    
    # Default: all days billable unless proven otherwise
    billable_days = total_days
    questionable_days = 0
    warning = ""
    details = ""
    
    if is_recovery_type(contract):
        # For Recovery/T&R, notice timing affects collectibility
        deadline_days = TOW_RECOVERY_SCHEDULE["lien_notice_deadline_days"]
        
        if contract.first_notice_sent_date:
            first_notice_sent = parse_date(contract.first_notice_sent_date)
            days_to_notice = (first_notice_sent.date() - start.date()).days
            
            if days_to_notice > deadline_days:
                # Notice sent late - days after deadline may be questionable
                late_by = days_to_notice - deadline_days
                questionable_days = min(late_by, total_days)
                billable_days = total_days - questionable_days
                
                warning = (
                    f"⚠️ COLLECTIBILITY RISK: Lien notice sent {late_by} days late. "
                    f"Storage charges for {questionable_days} days (after {deadline_days}-day deadline) "
                    f"may not be legally collectible from vehicle owner under Florida 713.78."
                )
                details = (
                    f"Notice sent on day {days_to_notice} (due by day {deadline_days}). "
                    f"Of {total_days} total storage days: {billable_days} days are clearly billable, "
                    f"{questionable_days} days may be disputed by owner."
                )
            else:
                # Notice sent on time - all days billable
                details = (
                    f"Lien notice sent within {deadline_days}-day deadline (sent on day {days_to_notice}). "
                    f"All {total_days} storage days are billable under Florida 713.78."
                )
        else:
            # Notice not sent yet
            days_since_start = (as_of.date() - start.date()).days
            
            if days_since_start > deadline_days:
                # Past deadline without notice - all days after deadline are questionable
                overdue_by = days_since_start - deadline_days
                questionable_days = overdue_by
                billable_days = deadline_days  # Only days up to deadline are clearly billable
                
                warning = (
                    f"⚠️ COLLECTIBILITY RISK: Lien notice not sent (overdue by {overdue_by} days). "
                    f"Storage charges for {questionable_days} days (after {deadline_days}-day deadline) "
                    f"may not be legally collectible from vehicle owner under Florida 713.78."
                )
                details = (
                    f"Notice deadline was day {deadline_days}, now on day {days_since_start}. "
                    f"Of {total_days} total storage days: {billable_days} days may be billable, "
                    f"{questionable_days} days are at risk of being uncollectible."
                )
            else:
                # Still within deadline window
                details = (
                    f"Notice deadline is day {deadline_days} (currently day {days_since_start}). "
                    f"All {total_days} storage days remain billable if notice sent on time."
                )
    else:
        # Storage Only - more lenient, notices are recommendations
        details = (
            f"Storage Only contract: All {total_days} storage days are billable. "
            f"Notice timing does not affect storage fee collectibility for this contract type."
        )
    
    return {
        "total_days": total_days,
        "billable_days": billable_days,
        "questionable_days": questionable_days,
        "warning": warning,
        "details": details,
    }


def balance(contract: StorageContract, as_of: datetime | None = None, include_breakdown: bool = False) -> float | Dict[str, any]:
    """
    Calculate outstanding balance.
    
    Args:
        contract: The storage contract
        as_of: Date to calculate balance as of (default: today)
        include_breakdown: If True, return dict with balance and storage days breakdown
    
    Returns:
        If include_breakdown=False: float balance amount
        If include_breakdown=True: dict with 'balance' and 'breakdown' keys
    """
    charges = calculate_charges(contract, as_of)
    total_charges = charges["subtotal"]
    balance_amount = round(total_charges - total_payments(contract), 2)
    
    if include_breakdown:
        breakdown = storage_days_breakdown(contract, as_of)
        return {
            "balance": balance_amount,
            "breakdown": breakdown,
        }
    
    return balance_amount


def past_due_status(contract: StorageContract, as_of: datetime | None = None) -> Tuple[bool, int]:
    """Check if contract is past due. Delegates to specialized modules."""
    contract_type = contract.contract_type.lower()
    
    if contract_type == "tow":
        return tow_logic.tow_past_due_status(contract)
    elif contract_type == "recovery":
        return recovery_logic.recovery_past_due_status(contract)
    else:  # storage
        return storage_logic.storage_past_due_status(contract)


def lien_eligibility(contract: StorageContract, as_of: datetime | None = None) -> Tuple[bool, str]:
    """
    Return (is_lien_eligible: bool, lien_status_text: str).
    
    For Tow & Recovery: Based on Florida 713.78 - lien eligible after notice sent within 7 days.
    For Storage Only: Based on STORAGE_ONLY_SCHEDULE - lien eligible after configured days from start.
    """
    as_of = as_of or datetime.today()
    start = parse_date(contract.start_date)
    
    is_eligible = False
    status_text = "Active"
    
    if is_recovery_type(contract):
        # Recovery/T&R: Lien eligible once notice is sent within deadline
        if contract.first_notice_sent_date:
            first_notice_sent = parse_date(contract.first_notice_sent_date)
            days_from_start = (first_notice_sent.date() - start.date()).days
            
            if days_from_start <= TOW_RECOVERY_SCHEDULE["lien_notice_deadline_days"]:
                is_eligible = True
                status_text = "Lien Eligible"
            else:
                is_eligible = False
                status_text = "Invalid (notice sent late)"
        else:
            days_since_start = (as_of.date() - start.date()).days
            if days_since_start > TOW_RECOVERY_SCHEDULE["lien_notice_deadline_days"]:
                status_text = "Notice Overdue"
            else:
                status_text = "Active"
            is_eligible = False
    else:
        # Storage Only: Lien eligible after configured days from start
        lien_eligible_date = start + timedelta(days=STORAGE_ONLY_SCHEDULE["lien_eligible_days"])
        
        if as_of.date() >= lien_eligible_date.date():
            is_eligible = True
            status_text = "Lien Eligible"
        else:
            days_remaining = (lien_eligible_date.date() - as_of.date()).days
            status_text = f"Active ({days_remaining} days until lien eligible)"
            is_eligible = False
    
    return is_eligible, status_text


def lien_timeline(contract: StorageContract) -> Dict[str, any]:
    """
    Return dict with lien timeline, notice requirements, and sale eligibility.
    
    Delegates to specialized modules based on contract type:
    - Storage: storage_logic.storage_lien_timeline()
    - Tow: tow_logic.tow_no_lien_applicable() (voluntary tows don't have liens)
    - Recovery: recovery_logic.recovery_lien_timeline() (only if licensed)
    
    NOTE: Recovery features require ENABLE_INVOLUNTARY_TOWS = True in config.py
    """
    contract_type = contract.contract_type.lower()
    
    if contract_type == "tow":
        return tow_logic.tow_no_lien_applicable()
    elif contract_type == "recovery" and ENABLE_INVOLUNTARY_TOWS:
        return recovery_logic.recovery_lien_timeline(contract)
    else:  # storage (or recovery when disabled, treat as storage)
        return storage_logic.storage_lien_timeline(contract)


def lien_timeline_legacy(contract: StorageContract) -> Dict[str, any]:
    """
    LEGACY VERSION - kept for backward compatibility.
    New code should use contract-specific functions from specialized modules.
    
    Uses different schedules based on contract type:
    - Tow & Recovery: Florida Statute 713.78 rules (TOW_RECOVERY_SCHEDULE)
    - Storage Only: Configurable storage schedule (STORAGE_ONLY_SCHEDULE)
    
    Returns structured data with dates, eligibility flags, and validation warnings.
    """
    start = parse_date(contract.start_date)
    as_of = datetime.today()
    warnings = []
    
    if is_recovery_type(contract):
        # ===== RECOVERY / TOW & RECOVERY (Florida 713.78) =====
        is_lien_eligible = False
        is_sale_eligible = False
        
        # Lien notice must be sent within deadline
        lien_notice_deadline = start + timedelta(days=TOW_RECOVERY_SCHEDULE["lien_notice_deadline_days"])
        
        if contract.first_notice_sent_date:
            first_notice_sent = parse_date(contract.first_notice_sent_date)
            days_from_start = (first_notice_sent.date() - start.date()).days
            
            # Validate notice timing
            if days_from_start > TOW_RECOVERY_SCHEDULE["lien_notice_deadline_days"]:
                warnings.append(
                    f"⚠️ Lien notice sent {days_from_start} days after storage date "
                    f"(must be within {TOW_RECOVERY_SCHEDULE['lien_notice_deadline_days']} business days)"
                )
                lien_eligible_date = "Invalid (notice sent late)"
                sale_earliest_date = "Invalid (notice sent late)"
                is_lien_eligible = False
                is_sale_eligible = False
            else:
                # Notice sent on time
                is_lien_eligible = True
                lien_eligible_date = first_notice_sent.strftime(DATE_FORMAT)
                
                # Calculate sale date based on vehicle age
                current_year = as_of.year
                vehicle_year = contract.vehicle.year if contract.vehicle.year else current_year
                vehicle_age = current_year - vehicle_year
                
                # Determine wait period by vehicle age
                if vehicle_age >= TOW_RECOVERY_SCHEDULE["vehicle_age_threshold"]:
                    sale_wait_days = TOW_RECOVERY_SCHEDULE["sale_wait_days_old_vehicle"]
                else:
                    sale_wait_days = TOW_RECOVERY_SCHEDULE["sale_wait_days_new_vehicle"]
                
                # Calculate earliest sale date
                sale_date = first_notice_sent + timedelta(days=sale_wait_days)
                
                # Enforce minimum notice-to-sale gap
                min_sale_date = first_notice_sent + timedelta(days=TOW_RECOVERY_SCHEDULE["min_notice_to_sale_days"])
                if sale_date < min_sale_date:
                    sale_date = min_sale_date
                    warnings.append(
                        f"ℹ️ Sale date adjusted to meet {TOW_RECOVERY_SCHEDULE['min_notice_to_sale_days']}-day "
                        "minimum after notice"
                    )
                
                sale_earliest_date = sale_date.strftime(DATE_FORMAT)
                
                # Check sale eligibility
                if as_of.date() >= sale_date.date():
                    is_sale_eligible = True
                    warnings.append("✓ SALE ELIGIBLE - Contact legal for sale process")
                else:
                    days_until_sale = (sale_date.date() - as_of.date()).days
                    warnings.append(
                        f"Lien notice sent on time - Sale eligible in {days_until_sale} days "
                        f"(vehicle is {vehicle_age} years old, requires {sale_wait_days} day wait)"
                    )
        else:
            # Notice not sent yet
            days_since_start = (as_of.date() - start.date()).days
            deadline_days = TOW_RECOVERY_SCHEDULE["lien_notice_deadline_days"]
            
            if days_since_start > deadline_days:
                warnings.append(
                    f"⚠️ Lien notice overdue by {days_since_start - deadline_days} days "
                    f"(must be sent within {deadline_days} business days of storage date)"
                )
            else:
                warnings.append(
                    f"Lien notice due by {lien_notice_deadline.strftime(DATE_FORMAT)} "
                    f"({deadline_days - days_since_start} days remaining)"
                )
            
            lien_eligible_date = "Pending (notice not sent)"
            sale_earliest_date = "Pending (notice not sent)"
        
        return {
            "first_notice_due": lien_notice_deadline.strftime(DATE_FORMAT),
            "first_notice_sent": contract.first_notice_sent_date or "Not sent",
            "lien_eligible_date": lien_eligible_date,
            "is_lien_eligible": is_lien_eligible,
            "sale_earliest_date": sale_earliest_date,
            "is_sale_eligible": is_sale_eligible,
            "warnings": warnings,
        }
    
    else:
        # ===== STORAGE ONLY (Configurable Schedule) =====
        schedule = STORAGE_ONLY_SCHEDULE
        
        # Calculate milestone dates
        first_notice_date = start + timedelta(days=schedule["first_notice_days"])
        second_notice_date = start + timedelta(days=schedule["second_notice_days"])
        lien_eligible_date = start + timedelta(days=schedule["lien_eligible_days"])
        sale_eligible_date = start + timedelta(days=schedule["sale_eligible_days"])
        
        # Check current status
        is_lien_eligible = as_of.date() >= lien_eligible_date.date()
        is_sale_eligible = as_of.date() >= sale_eligible_date.date()
        
        # Generate status messages
        if is_sale_eligible:
            warnings.append("✓ SALE ELIGIBLE - Contract has reached sale eligibility date")
        elif is_lien_eligible:
            days_until_sale = (sale_eligible_date.date() - as_of.date()).days
            warnings.append(f"✓ Lien eligible - Sale eligible in {days_until_sale} days")
        else:
            days_until_lien = (lien_eligible_date.date() - as_of.date()).days
            warnings.append(f"Storage period in progress - Lien eligible in {days_until_lien} days")
        
        # Notice reminders
        if not contract.first_notice_sent_date and as_of.date() >= first_notice_date.date():
            warnings.append(f"ℹ️ First notice recommended (eligible since {first_notice_date.strftime(DATE_FORMAT)})")
        
        if not contract.second_notice_sent_date and as_of.date() >= second_notice_date.date():
            warnings.append(f"ℹ️ Second notice recommended (eligible since {second_notice_date.strftime(DATE_FORMAT)})")
        
        return {
            "first_notice_due": first_notice_date.strftime(DATE_FORMAT),
            "first_notice_sent": contract.first_notice_sent_date or "Not sent",
            "second_notice_due": second_notice_date.strftime(DATE_FORMAT),
            "second_notice_sent": contract.second_notice_sent_date or "Not sent",
            "lien_eligible_date": lien_eligible_date.strftime(DATE_FORMAT),
            "is_lien_eligible": is_lien_eligible,
            "sale_earliest_date": sale_eligible_date.strftime(DATE_FORMAT),
            "is_sale_eligible": is_sale_eligible,
            "warnings": warnings,
        }


def record_payment(contract: StorageContract, amount: float, method: str, note: str, date: str | None = None) -> Payment:
    payment = Payment(
        date=date or datetime.today().strftime(DATE_FORMAT),
        amount=amount,
        method=method,
        note=note,
    )
    contract.payments.append(payment)
    return payment


def add_notice(contract: StorageContract, notice_type: str, amount_due: float, notes: str = "") -> Notice:
    today = datetime.today().strftime(DATE_FORMAT)
    notice = Notice(
        notice_type=notice_type,
        date_generated=today,
        amount_due=amount_due,
        notes=notes,
    )
    contract.notices.append(notice)
    return notice


def format_payments_block(contract_or_payments) -> list[str]:
    """Return a list of lines representing the payments table.

    Accepts either a StorageContract instance (with a .payments list) or a
    list/iterable of payment objects or dicts. Each payment may be a dataclass
    with attributes `date`, `amount`, `method`, `note` or a dict with those
    keys.
    """
    # Determine payments iterable
    payments = getattr(contract_or_payments, "payments", None)
    if payments is None:
        payments = contract_or_payments or []

    lines: list[str] = []
    lines.append("")
    lines.append("Payments Recorded:")
    # Header
    if payments:
        lines.append(f"{'Date':<12} {'Amount':<10} {'Method':<15} {'Note':<30}")
        lines.append("-" * 67)
        for p in payments:
            if isinstance(p, dict):
                date = p.get("date", "")
                amount = p.get("amount", 0.0)
                method = p.get("method", "")
                note = p.get("note", "")
            else:
                date = getattr(p, "date", "")
                amount = getattr(p, "amount", 0.0)
                method = getattr(p, "method", "")
                note = getattr(p, "note", "")
            try:
                amount_str = f"${float(amount):.2f}"
            except Exception:
                amount_str = str(amount)
            lines.append(f"{date:<12} {amount_str:<10} {str(method):<15} {str(note):<30}")
    else:
        lines.append("- None recorded")
    return lines




def format_contract_summary(contract: StorageContract, as_of: datetime | None = None) -> str:
    as_of = as_of or datetime.today()
    charges = calculate_charges(contract, as_of)
    bal = balance(contract, as_of)
    lien_dates = lien_timeline(contract)
    is_lien_eligible, lien_status = lien_eligibility(contract, as_of)
    lines = [
        "Storage & Recovery Contract Summary",
        "-----------------------------------",
        f"Contract #: {contract.contract_id}",
        f"Customer: {contract.customer.name} | {contract.customer.phone}",
        f"Address: {contract.customer.address}",
        f"Vehicle: {contract.vehicle.vehicle_type} {contract.vehicle.make} {contract.vehicle.model} ({contract.vehicle.plate})",
        f"VIN: {contract.vehicle.vin} | Color: {contract.vehicle.color}",
        f"Start Date: {contract.start_date}",
        f"Contract Type: {contract.contract_type.title()}",
        f"Rate Mode: {contract.rate_mode.title()}",
        f"Admin Fee: ${charges.get('admin', 0):.2f}",
        f"Storage Accrued ({storage_days(contract, as_of)} days): ${charges['storage']:.2f}",
        f"Tow Fees: ${charges.get('tow_fees', 0):.2f}",
        f"Recovery Fees: ${charges.get('recovery', 0):.2f}",
        f"Payments: ${total_payments(contract):.2f}",
        f"Balance as of {as_of.strftime(DATE_FORMAT)}: ${bal:.2f}",
        "",
        "Lien Timeline:",
        f"  First notice due: {lien_dates.get('first_notice_due', 'N/A')}",
        f"  First notice sent: {lien_dates.get('first_notice_sent', 'Not sent')}",
        f"  Lien eligible: {lien_dates.get('lien_eligible_date', 'N/A')} ({'Eligible' if lien_dates.get('is_lien_eligible') else 'Not yet'})",
        f"  Earliest sale date: {lien_dates.get('sale_earliest_date', 'N/A')}",
        f"  Lien status: {lien_status}",
        "",
        "Notices Sent:",
    ]
    if contract.notices:
        for n in contract.notices:
            date_shown = n.date_sent if n.date_sent else n.date_generated
            lines.append(f"- {n.notice_type} sent {date_shown} | Due ${n.amount_due:.2f} | {n.notes}")
    else:
        lines.append("- None recorded")

    if contract.notes:
        lines.append("\nNotes:")
        for note in contract.notes:
            lines.append(f"- {note}")

    if contract.attachments:
        lines.append("\nAttachments (paths only):")
        for path in contract.attachments:
            lines.append(f"- {path}")

    # Append payments block
    lines.extend(format_payments_block(contract))

    return "\n".join(lines)


def format_contract_record(contract: StorageContract, as_of: datetime | None = None) -> str:
    """
    Format contract summary with detailed payment listing.
    Used for printing or file export.
    """
    as_of = as_of or datetime.today()
    charges = calculate_charges(contract, as_of)
    bal = balance(contract, as_of)
    lien_dates = lien_timeline(contract)
    is_lien_eligible, lien_status = lien_eligibility(contract, as_of)
    
    # Determine storage rate based on mode and calculate date range
    days = storage_days(contract, as_of)
    start_dt = parse_date(contract.start_date)
    end_dt = as_of
    date_range = f"{start_dt.strftime('%b %d')} – {end_dt.strftime('%b %d')}"
    
    if contract.rate_mode == "weekly":
        storage_rate_display = f"Weekly Rate: ${contract.weekly_storage_fee:.2f}"
        storage_detail = f"Storage: ${charges['storage']:.2f} (Weekly rate, {date_range}, {days} days)"
    elif contract.rate_mode == "monthly":
        storage_rate_display = f"Monthly Rate: ${contract.monthly_storage_fee:.2f}"
        storage_detail = f"Storage: ${charges['storage']:.2f} (Monthly rate, {date_range}, {days} days)"
    else:
        storage_rate_display = f"Daily Rate: ${contract.daily_storage_fee:.2f}"
        storage_detail = f"Storage: ${charges['storage']:.2f} (Daily rate, {date_range}, {days} days)"
    
    lines = [
        "Storage & Recovery Contract Record",
        "==================================",
        f"Contract #: {contract.contract_id}",
        f"Contract Type: {contract.contract_type.title()}",
        f"Customer: {contract.customer.name} | {contract.customer.phone}",
        f"Address: {contract.customer.address}",
        f"Vehicle: {contract.vehicle.vehicle_type} {contract.vehicle.make} {contract.vehicle.model} ({contract.vehicle.plate})",
        f"VIN: {contract.vehicle.vin} | Color: {contract.vehicle.color}",
        f"Start Date: {contract.start_date}",
        storage_rate_display,
        f"Admin Fee: ${contract.admin_fee:.2f}",
        "",
        "CHARGES BREAKDOWN:",
        f"  {storage_detail}",
        f"  Tow Fees: ${charges.get('tow_fees', 0.0):.2f}",
        f"  Recovery Fees: ${charges.get('recovery_fees', 0.0):.2f}",
        f"  Admin: ${charges['admin']:.2f}",
        f"  Total Charges: ${charges['subtotal']:.2f}",
        f"  Total Payments: ${total_payments(contract):.2f}",
        f"  BALANCE as of {as_of.strftime(DATE_FORMAT)}: ${bal:.2f}",
        "",
        "Lien Timeline:",
        f"  First notice due: {lien_dates.get('first_notice_due', 'N/A')}",
        f"  First notice sent: {lien_dates.get('first_notice_sent', 'Not sent')}",
        f"  Lien eligible: {lien_dates.get('lien_eligible_date', 'N/A')} ({'Eligible' if lien_dates.get('is_lien_eligible') else 'Not yet'})",
        f"  Earliest sale date: {lien_dates.get('sale_earliest_date', 'N/A')}",
        f"  Lien status: {lien_status}",
        "",
        "Notices Sent:",
    ]
    if contract.notices:
        for n in contract.notices:
            date_shown = n.date_sent if n.date_sent else n.date_generated
            lines.append(f"- {n.notice_type} sent {date_shown} | Due ${n.amount_due:.2f} | {n.notes}")
    else:
        lines.append("- None recorded")

    # Payments (use shared helper)
    lines.extend(format_payments_block(contract))

    if contract.notes:
        lines.append("")
        lines.append("Notes:")
        for note in contract.notes:
            lines.append(f"- {note}")

    if contract.attachments:
        lines.append("")
        lines.append("Attachments (paths only):")
        for path in contract.attachments:
            lines.append(f"- {path}")

    return "\n".join(lines)
