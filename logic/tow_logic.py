"""Tow-only contract business logic.

Tow contracts are for voluntary towing services.
- Customer requested the tow (not involuntary)
- No lien process (voluntary agreement)
- Payment expected within 7 days
- Storage fees apply if vehicle not picked up
- Florida allows exemption: no storage charge if vehicle on lot < 6 hours
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Tuple

from models.lot_models import StorageContract, DATE_FORMAT
from utils.config import TOW_STORAGE_EXEMPTION_HOURS

# Tow contracts don't have lien process (voluntary service)
TOW_PAYMENT_EXPECTATION_DAYS = 7

LABOR_BLOCK_MINUTES = 15


def calculate_tow_fees(contract: StorageContract) -> float:
    """Calculate tow service fees for voluntary tow contract.
    
    Includes:
    - Base tow fee
    - Mileage charges (if over included miles)
    - Labor charges (if extra labor needed)
    - After hours fee (if applicable)
    
    Args:
        contract: Tow contract with fee details
        
    Returns:
        Total tow service fees in dollars
    """
    total = 0.0
    
    # Base tow fee
    total += contract.tow_base_fee
    
    # Mileage charges
    if contract.recovery_miles > contract.mileage_included:
        extra_miles = contract.recovery_miles - contract.mileage_included
        total += extra_miles * contract.mileage_rate
    
    # Labor charges (billed in 15-minute blocks)
    if contract.extra_labor_minutes > 0:
        blocks = math.ceil(contract.extra_labor_minutes / LABOR_BLOCK_MINUTES)
        hourly_rate = contract.labor_rate_per_hour
        block_rate = (hourly_rate / 60) * LABOR_BLOCK_MINUTES
        total += blocks * block_rate
    
    # After hours fee (stored in impound_fee field for tow contracts)
    if hasattr(contract, 'impound_fee') and contract.impound_fee > 0:
        total += contract.impound_fee
    
    return round(total, 2)


def calculate_tow_storage_fees(contract: StorageContract, as_of_date: datetime = None) -> float:
    """Calculate storage fees for tow contract.
    
    If customer doesn't pick up vehicle immediately, storage fees apply.
    Florida exemption: No storage charge if vehicle on lot < 6 hours.
    Uses explicit daily/weekly/monthly rates from contract.
    
    Args:
        contract: Tow contract with rate_mode and storage fees
        as_of_date: Date to calculate through (default: today)
        
    Returns:
        Total storage fees in dollars
    """
    if as_of_date is None:
        as_of_date = datetime.now()
    
    start = datetime.strptime(contract.start_date, DATE_FORMAT)
    
    # Calculate time on lot
    time_on_lot = as_of_date - start
    hours_on_lot = time_on_lot.total_seconds() / 3600
    
    # Florida exemption: No storage charge if on lot < 6 hours
    if hours_on_lot < TOW_STORAGE_EXEMPTION_HOURS:
        return 0.0
    
    # Calculate full days (exemption doesn't affect day calculation)
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


def tow_past_due_status(contract: StorageContract) -> Tuple[bool, int]:
    """Check if tow contract is past due.
    
    Voluntary tows expected to be paid within 7 days.
    
    Args:
        contract: Tow contract
        
    Returns:
        Tuple of (is_past_due, days_overdue)
    """
    start = datetime.strptime(contract.start_date, DATE_FORMAT)
    payment_due = start + timedelta(days=TOW_PAYMENT_EXPECTATION_DAYS)
    today = datetime.now()
    
    if today > payment_due:
        days_overdue = (today - payment_due).days
        return (True, days_overdue)
    else:
        return (False, 0)


def tow_no_lien_applicable() -> dict:
    """Return message that liens don't apply to voluntary tow contracts.
    
    Tow contracts are voluntary services - no lien process.
    
    Returns:
        Dictionary with N/A values and explanation
    """
    return {
        "first_notice_due": "N/A (voluntary tow)",
        "first_notice_sent": "N/A (voluntary tow)",
        "lien_eligible_date": "N/A (voluntary tow)",
        "is_lien_eligible": False,
        "sale_earliest_date": "N/A (voluntary tow)",
        "is_sale_eligible": False,
        "warnings": ["ℹ️ Voluntary tow contracts do not have lien process. Payment expected within 7 days."],
    }


def validate_tow_contract(contract: StorageContract) -> list[str]:
    """Validate tow contract has required fields.
    
    Args:
        contract: Tow contract to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    if not contract.customer or not contract.customer.name:
        errors.append("Customer name required")
    
    if not contract.customer or not contract.customer.phone:
        errors.append("Customer phone required")
    
    if not contract.vehicle or not contract.vehicle.make:
        errors.append("Vehicle make required")
    
    if not contract.vehicle or not contract.vehicle.model:
        errors.append("Vehicle model required")
    
    if not contract.start_date:
        errors.append("Start date required")
    
    if contract.tow_base_fee < 0:
        errors.append("Tow base fee cannot be negative")
    
    if contract.daily_storage_fee < 0:
        errors.append("Daily storage fee cannot be negative")
    
    if contract.admin_fee > 250:
        errors.append("Admin fee cannot exceed $250 (Florida requirement)")
    
    return errors
