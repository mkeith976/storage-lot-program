"""Business logic and persistence helpers for the lot application."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

from lot_models import (
    DATE_FORMAT,
    Customer,
    Fee,
    Notice,
    Payment,
    StorageContract,
    StorageData,
    Vehicle,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "lot_data.json"
FEE_TEMPLATE_PATH = BASE_DIR / "fee_templates.json"

FIRST_NOTICE_DAYS = 30
SECOND_NOTICE_DAYS = 45
LIEN_NOTICE_DAYS = 60
LIEN_BUFFER_DAYS = 10
LABOR_BLOCK_MINUTES = 15

DEFAULT_VEHICLE_FEES: Dict[str, Dict[str, float]] = {
    "Car": {
        "daily_rate": 35.0,
        "tow_fee": 150.0,
        "impound_fee": 75.0,
        "admin_fee": 25.0,
        "tow_base_fee": 150.0,
        "mileage_included": 5.0,
        "mileage_rate": 3.5,
        "labor_rate": 45.0,
        "certified_mail_fee_first": 8.5,
        "certified_mail_fee_second": 8.5,
    },
    "Truck": {
        "daily_rate": 42.0,
        "tow_fee": 175.0,
        "impound_fee": 85.0,
        "admin_fee": 30.0,
        "tow_base_fee": 175.0,
        "mileage_included": 5.0,
        "mileage_rate": 4.0,
        "labor_rate": 55.0,
        "certified_mail_fee_first": 8.5,
        "certified_mail_fee_second": 8.5,
    },
    "Motorcycle": {
        "daily_rate": 25.0,
        "tow_fee": 120.0,
        "impound_fee": 60.0,
        "admin_fee": 20.0,
        "tow_base_fee": 120.0,
        "mileage_included": 5.0,
        "mileage_rate": 3.0,
        "labor_rate": 45.0,
        "certified_mail_fee_first": 8.5,
        "certified_mail_fee_second": 8.5,
    },
    "RV": {
        "daily_rate": 60.0,
        "tow_fee": 250.0,
        "impound_fee": 125.0,
        "admin_fee": 40.0,
        "tow_base_fee": 250.0,
        "mileage_included": 5.0,
        "mileage_rate": 6.0,
        "labor_rate": 65.0,
        "certified_mail_fee_first": 8.5,
        "certified_mail_fee_second": 8.5,
    },
    "Boat": {
        "daily_rate": 55.0,
        "tow_fee": 225.0,
        "impound_fee": 120.0,
        "admin_fee": 40.0,
        "tow_base_fee": 225.0,
        "mileage_included": 5.0,
        "mileage_rate": 5.0,
        "labor_rate": 60.0,
        "certified_mail_fee_first": 8.5,
        "certified_mail_fee_second": 8.5,
    },
    "Trailer": {
        "daily_rate": 28.0,
        "tow_fee": 130.0,
        "impound_fee": 65.0,
        "admin_fee": 22.0,
        "tow_base_fee": 130.0,
        "mileage_included": 5.0,
        "mileage_rate": 3.0,
        "labor_rate": 45.0,
        "certified_mail_fee_first": 8.5,
        "certified_mail_fee_second": 8.5,
    },
    "Car": {"daily_rate": 35.0, "tow_fee": 150.0, "impound_fee": 75.0, "admin_fee": 25.0},
    "Truck": {"daily_rate": 42.0, "tow_fee": 175.0, "impound_fee": 85.0, "admin_fee": 30.0},
    "Motorcycle": {"daily_rate": 25.0, "tow_fee": 120.0, "impound_fee": 60.0, "admin_fee": 20.0},
    "RV": {"daily_rate": 60.0, "tow_fee": 250.0, "impound_fee": 125.0, "admin_fee": 40.0},
    "Boat": {"daily_rate": 55.0, "tow_fee": 225.0, "impound_fee": 120.0, "admin_fee": 40.0},
    "Trailer": {"daily_rate": 28.0, "tow_fee": 130.0, "impound_fee": 65.0, "admin_fee": 22.0},
}
FEE_TEMPLATES: Dict[str, Dict[str, float]] = {}


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def load_data(path: Path = DATA_PATH) -> StorageData:
    if not path.exists():
        return StorageData()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return StorageData.from_dict(data)
    except Exception:
        return StorageData()


def save_data(data: StorageData, path: Path = DATA_PATH) -> None:
    path.write_text(json.dumps(data.to_dict(), indent=2), encoding="utf-8")


def load_fee_templates(path: Path = FEE_TEMPLATE_PATH) -> Dict[str, Dict[str, float]]:
    if not path.exists():
        return DEFAULT_VEHICLE_FEES.copy()
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
        merged: Dict[str, Dict[str, float]] = DEFAULT_VEHICLE_FEES.copy()
        for k, v in loaded.items():
            if isinstance(v, dict):
                default = DEFAULT_VEHICLE_FEES.get(k, DEFAULT_VEHICLE_FEES.get("Car", {}))
                merged[k] = {
                    "daily_rate": float(v.get("daily_rate", default.get("daily_rate", 0.0))),
                    "tow_fee": float(v.get("tow_fee", default.get("tow_fee", 0.0))),
                    "impound_fee": float(v.get("impound_fee", default.get("impound_fee", 0.0))),
                    "admin_fee": float(v.get("admin_fee", default.get("admin_fee", 0.0))),
                    "tow_base_fee": float(v.get("tow_base_fee", default.get("tow_base_fee", 0.0))),
                    "mileage_included": float(v.get("mileage_included", default.get("mileage_included", 0.0))),
                    "mileage_rate": float(v.get("mileage_rate", default.get("mileage_rate", 0.0))),
                    "labor_rate": float(v.get("labor_rate", default.get("labor_rate", 0.0))),
                    "certified_mail_fee_first": float(
                        v.get("certified_mail_fee_first", default.get("certified_mail_fee_first", 0.0))
                    ),
                    "certified_mail_fee_second": float(
                        v.get("certified_mail_fee_second", default.get("certified_mail_fee_second", 0.0))
                    ),
                merged[k] = {
                    "daily_rate": float(v.get("daily_rate", DEFAULT_VEHICLE_FEES.get(k, {}).get("daily_rate", 0.0))),
                    "tow_fee": float(v.get("tow_fee", DEFAULT_VEHICLE_FEES.get(k, {}).get("tow_fee", 0.0))),
                    "impound_fee": float(v.get("impound_fee", DEFAULT_VEHICLE_FEES.get(k, {}).get("impound_fee", 0.0))),
                    "admin_fee": float(v.get("admin_fee", DEFAULT_VEHICLE_FEES.get(k, {}).get("admin_fee", 0.0))),
                }
        return merged
    except Exception:
        return DEFAULT_VEHICLE_FEES.copy()


def save_fee_templates(templates: Dict[str, Dict[str, float]], path: Path = FEE_TEMPLATE_PATH) -> None:
    path.write_text(json.dumps(templates, indent=2), encoding="utf-8")


FEE_TEMPLATES = load_fee_templates()


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
    extra_labor_minutes: float,
    labor_rate_per_hour: float,
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
        extra_labor_minutes=extra_labor_minutes,
        labor_rate_per_hour=labor_rate_per_hour,
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
    days = storage_days(contract, as_of)
    storage_charge = round(days * contract.daily_rate, 2)
    recovery_charge = round(
        contract.tow_base_fee
        + recovery_mileage_fee(contract)
        + contract.certified_mail_fee_first
        + contract.certified_mail_fee_second,
        2,
    )
def calculate_charges(contract: StorageContract, as_of: datetime | None = None) -> Dict[str, float]:
    days = storage_days(contract, as_of)
    storage_charge = round(days * contract.daily_rate, 2)
    result = {
        "storage": storage_charge,
        "tow_impound": round(contract.tow_fee + contract.impound_fee, 2),
        "admin": round(contract.admin_fee, 2),
        "labor": labor_fee(contract),
        "recovery": recovery_charge,
    }
    result["subtotal"] = round(sum(result.values()), 2)
    return result


def total_payments(contract: StorageContract) -> float:
    return round(sum(p.amount for p in contract.payments), 2)


def balance(contract: StorageContract, as_of: datetime | None = None) -> float:
    charges = calculate_charges(contract, as_of)
    total_charges = charges["subtotal"]
    return round(total_charges - total_payments(contract), 2)


def past_due_status(contract: StorageContract, as_of: datetime | None = None) -> Tuple[bool, int]:
    as_of = as_of or datetime.today()
    days = storage_days(contract, as_of)
    grace_days = 7
    past_due_days = max(0, days - grace_days)
    return past_due_days > 0 and balance(contract, as_of) > 0, past_due_days


def lien_eligibility(contract: StorageContract, as_of: datetime | None = None) -> Tuple[str, str, str, str]:
    as_of = as_of or datetime.today()
    first = contract.first_notice_sent_date or (parse_date(contract.start_date) + timedelta(days=FIRST_NOTICE_DAYS)).strftime(
        DATE_FORMAT
    )
    second = contract.second_notice_sent_date or (
        parse_date(contract.start_date) + timedelta(days=SECOND_NOTICE_DAYS)
    ).strftime(DATE_FORMAT)
    eligible_date = contract.lien_eligible_date or (
        parse_date(contract.start_date) + timedelta(days=LIEN_NOTICE_DAYS + LIEN_BUFFER_DAYS)
    ).strftime(DATE_FORMAT)
    status: str
    try:
        eligible_dt = parse_date(eligible_date)
        if as_of.date() < eligible_dt.date():
            status = "Not Eligible"
        elif as_of.date() == eligible_dt.date():
            status = "Lien Eligible"
        else:
            status = "Past Lien Date"
    except Exception:
        status = "Not Eligible"
    return first, second, eligible_date, status


def lien_timeline(contract: StorageContract) -> Dict[str, str]:
    start = parse_date(contract.start_date)
    first_notice = start + timedelta(days=FIRST_NOTICE_DAYS)
    second_notice = start + timedelta(days=SECOND_NOTICE_DAYS)
    earliest_lien = start + timedelta(days=LIEN_NOTICE_DAYS + LIEN_BUFFER_DAYS)
    return {
        "first_notice": first_notice.strftime(DATE_FORMAT),
        "second_notice": second_notice.strftime(DATE_FORMAT),
        "earliest_lien": earliest_lien.strftime(DATE_FORMAT),
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


def format_contract_record(contract: StorageContract, as_of: datetime | None = None) -> str:
def format_contract_summary(contract: StorageContract, as_of: datetime | None = None) -> str:
    as_of = as_of or datetime.today()
    charges = calculate_charges(contract, as_of)
    bal = balance(contract, as_of)
    lien_dates = lien_timeline(contract)
    first_notice, second_notice, lien_eligible, lien_status = lien_eligibility(contract, as_of)
    lines = [
        "Storage & Recovery Print Record",
        "-----------------------------------",
        f"Contract #: {contract.contract_id}",
        f"Contract Type: {contract.contract_type}",
    lines = [
        "Storage & Recovery Contract Summary",
        "-----------------------------------",
        f"Contract #: {contract.contract_id}",
        f"Customer: {contract.customer.name} | {contract.customer.phone}",
        f"Address: {contract.customer.address}",
        f"Vehicle: {contract.vehicle.vehicle_type} {contract.vehicle.make} {contract.vehicle.model} ({contract.vehicle.plate})",
        f"VIN: {contract.vehicle.vin} | Color: {contract.vehicle.color}",
        f"Start Date: {contract.start_date}",
        f"Daily Rate: ${contract.daily_rate:.2f}",
        f"Tow/Impound: ${charges['tow_impound']:.2f}",
        f"Admin: ${charges['admin']:.2f}",
        f"Storage Accrued ({storage_days(contract, as_of)} days): ${charges['storage']:.2f}",
        f"Labor: ${charges['labor']:.2f}",
        f"Recovery (base/mileage/mail): ${charges['recovery']:.2f}",
        f"Recovery miles: {contract.recovery_miles} @ ${contract.mileage_rate:.2f}/mi (incl. {contract.mileage_included} mi)",
        f"Payments: ${total_payments(contract):.2f}",
        f"Balance as of {as_of.strftime(DATE_FORMAT)}: ${bal:.2f}",
        "",
        "Lien Timeline:",
        f"  First notice planned/sent: {first_notice}",
        f"  Second notice planned/sent: {second_notice}",
        f"  Earliest lien sale: {lien_dates['earliest_lien']}",
        f"  Lien eligibility date: {lien_eligible} ({lien_status})",
        f"  First notice: {lien_dates['first_notice']}",
        f"  Second notice: {lien_dates['second_notice']}",
        f"  Earliest lien sale: {lien_dates['earliest_lien']}",
        "",
        "Notices:",
    ]
    if contract.notices:
        for n in contract.notices:
            sent = f" sent {n.date_sent}" if n.date_sent else ""
            lines.append(f"- {n.notice_type} generated {n.date_generated}{sent} | Due ${n.amount_due:.2f} | {n.notes}")
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

    return "\n".join(lines)
