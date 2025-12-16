"""Data models for the Storage & Recovery Lot program."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

DATE_FORMAT = "%Y-%m-%d"


@dataclass
class Customer:
    name: str
    phone: str = ""
    address: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Customer":
        return Customer(
            name=data.get("name", ""),
            phone=data.get("phone", ""),
            address=data.get("address", ""),
        )


@dataclass
class Vehicle:
    plate: str
    vin: str = ""
    vehicle_type: str = "Car"
    make: str = ""
    model: str = ""
    year: Optional[int] = None
    color: str = ""
    initial_mileage: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Vehicle":
        year_val = data.get("year")
        if year_val is not None:
            try:
                year_val = int(year_val)
            except (ValueError, TypeError):
                year_val = None
        
        return Vehicle(
            plate=data.get("plate", ""),
            vin=data.get("vin", ""),
            vehicle_type=data.get("vehicle_type", "Car"),
            make=data.get("make", ""),
            model=data.get("model", ""),
            year=year_val,
            color=data.get("color", ""),
            initial_mileage=float(data.get("initial_mileage", 0.0) or 0.0),
        )


@dataclass
class Fee:
    name: str
    amount: float
    category: str = "storage"
    is_default: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Fee":
        return Fee(
            name=data.get("name", ""),
            amount=float(data.get("amount", 0.0) or 0.0),
            category=data.get("category", "storage"),
            is_default=bool(data.get("is_default", True)),
        )


@dataclass
class Payment:
    """Payment record for a contract.
    
    NOTE: Field name is 'note' (singular), not 'notes'.
    The from_dict() method supports both for backward compatibility.
    """
    date: str
    amount: float
    method: str = "cash"
    note: str = ""  # Singular: 'note' not 'notes'

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Payment":
        # Backward compatibility: support both 'note' (current) and 'notes' (legacy)
        note_value = data.get("note", data.get("notes", ""))
        return Payment(
            date=data.get("date") or datetime.today().strftime(DATE_FORMAT),
            amount=float(data.get("amount", 0.0) or 0.0),
            method=data.get("method", "cash"),
            note=note_value,
        )


@dataclass
class Notice:
    notice_type: str
    date_generated: str
    date_sent: Optional[str] = None
    amount_due: float = 0.0
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Notice":
        return Notice(
            notice_type=data.get("notice_type", "First"),
            date_generated=data.get("date_generated", ""),
            date_sent=data.get("date_sent"),
            amount_due=float(data.get("amount_due", 0.0) or 0.0),
            notes=data.get("notes", ""),
        )


@dataclass
class StorageContract:
    contract_id: int
    customer: Customer
    vehicle: Vehicle
    start_date: str
    contract_type: str  # "storage", "tow", or "recovery"
    
    # Storage rate mode
    rate_mode: str = "daily"  # "daily", "weekly", or "monthly"
    daily_storage_fee: float = 0.0
    weekly_storage_fee: float = 0.0
    monthly_storage_fee: float = 0.0
    
    # Tow contract fields (voluntary tows)
    tow_base_fee: float = 0.0
    tow_mileage_rate: float = 0.0
    tow_miles_used: float = 0.0
    tow_hourly_labor_rate: float = 0.0
    tow_labor_hours: float = 0.0
    tow_after_hours_fee: float = 0.0
    
    # Recovery contract fields (involuntary)
    recovery_handling_fee: float = 0.0
    lien_processing_fee: float = 0.0
    cert_mail_fee: float = 0.0
    title_search_fee: float = 0.0
    dmv_fee: float = 0.0
    sale_fee: float = 0.0
    notices_sent: int = 0
    
    # Common fees
    admin_fee: float = 0.0
    
    notes: List[str] = field(default_factory=lambda: [])
    attachments: List[str] = field(default_factory=lambda: [])
    payments: List[Payment] = field(default_factory=lambda: [])
    fees: List[Fee] = field(default_factory=lambda: [])
    notices: List[Notice] = field(default_factory=lambda: [])
    audit_log: List[str] = field(default_factory=lambda: [])  # Immutable timestamped history
    status: str = "Active"
    first_notice_sent_date: str = ""
    second_notice_sent_date: str = ""
    lien_eligible_date: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "customer": self.customer.to_dict(),
            "vehicle": self.vehicle.to_dict(),
            "start_date": self.start_date,
            "contract_type": self.contract_type,
            "rate_mode": self.rate_mode,
            "daily_storage_fee": self.daily_storage_fee,
            "weekly_storage_fee": self.weekly_storage_fee,
            "monthly_storage_fee": self.monthly_storage_fee,
            "tow_base_fee": self.tow_base_fee,
            "tow_mileage_rate": self.tow_mileage_rate,
            "tow_miles_used": self.tow_miles_used,
            "tow_hourly_labor_rate": self.tow_hourly_labor_rate,
            "tow_labor_hours": self.tow_labor_hours,
            "tow_after_hours_fee": self.tow_after_hours_fee,
            "recovery_handling_fee": self.recovery_handling_fee,
            "lien_processing_fee": self.lien_processing_fee,
            "cert_mail_fee": self.cert_mail_fee,
            "title_search_fee": self.title_search_fee,
            "dmv_fee": self.dmv_fee,
            "sale_fee": self.sale_fee,
            "notices_sent": self.notices_sent,
            "admin_fee": self.admin_fee,
            "notes": self.notes,
            "attachments": self.attachments,
            "payments": [p.to_dict() for p in self.payments],
            "fees": [f.to_dict() for f in self.fees],
            "notices": [n.to_dict() for n in self.notices],
            "audit_log": self.audit_log,
            "status": self.status,
            "first_notice_sent_date": self.first_notice_sent_date,
            "second_notice_sent_date": self.second_notice_sent_date,
            "lien_eligible_date": self.lien_eligible_date,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "StorageContract":
        return StorageContract(
            contract_id=int(data.get("contract_id", 0)),
            customer=Customer.from_dict(data.get("customer", {})),
            vehicle=Vehicle.from_dict(data.get("vehicle", {})),
            start_date=data.get("start_date", datetime.today().strftime(DATE_FORMAT)),
            contract_type=data.get("contract_type", "storage"),
            rate_mode=data.get("rate_mode", "daily"),
            daily_storage_fee=float(data.get("daily_storage_fee", 0.0) or 0.0),
            weekly_storage_fee=float(data.get("weekly_storage_fee", 0.0) or 0.0),
            monthly_storage_fee=float(data.get("monthly_storage_fee", 0.0) or 0.0),
            tow_base_fee=float(data.get("tow_base_fee", 0.0) or 0.0),
            tow_mileage_rate=float(data.get("tow_mileage_rate", 0.0) or 0.0),
            tow_miles_used=float(data.get("tow_miles_used", 0.0) or 0.0),
            tow_hourly_labor_rate=float(data.get("tow_hourly_labor_rate", 0.0) or 0.0),
            tow_labor_hours=float(data.get("tow_labor_hours", 0.0) or 0.0),
            tow_after_hours_fee=float(data.get("tow_after_hours_fee", 0.0) or 0.0),
            recovery_handling_fee=float(data.get("recovery_handling_fee", 0.0) or 0.0),
            lien_processing_fee=float(data.get("lien_processing_fee", 0.0) or 0.0),
            cert_mail_fee=float(data.get("cert_mail_fee", 0.0) or 0.0),
            title_search_fee=float(data.get("title_search_fee", 0.0) or 0.0),
            dmv_fee=float(data.get("dmv_fee", 0.0) or 0.0),
            sale_fee=float(data.get("sale_fee", 0.0) or 0.0),
            notices_sent=int(data.get("notices_sent", 0)),
            admin_fee=float(data.get("admin_fee", 0.0) or 0.0),
            notes=list(data.get("notes", [])),
            attachments=list(data.get("attachments", [])),
            payments=[Payment.from_dict(p) for p in data.get("payments", [])],
            fees=[Fee.from_dict(f) for f in data.get("fees", [])],
            notices=[Notice.from_dict(n) for n in data.get("notices", [])],
            audit_log=list(data.get("audit_log", [])),
            status=data.get("status", "Active"),
            first_notice_sent_date=data.get("first_notice_sent_date", ""),
            second_notice_sent_date=data.get("second_notice_sent_date", ""),
            lien_eligible_date=data.get("lien_eligible_date", ""),
        )


@dataclass
class StorageData:
    contracts: List[StorageContract] = field(default_factory=lambda: [])
    next_id: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "next_id": self.next_id,
            "contracts": [c.to_dict() for c in self.contracts],
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "StorageData":
        return StorageData(
            next_id=int(data.get("next_id", 1)),
            contracts=[StorageContract.from_dict(c) for c in data.get("contracts", [])],
        )
