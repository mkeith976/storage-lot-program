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
    color: str = ""
    initial_mileage: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Vehicle":
        return Vehicle(
            plate=data.get("plate", ""),
            vin=data.get("vin", ""),
            vehicle_type=data.get("vehicle_type", "Car"),
            make=data.get("make", ""),
            model=data.get("model", ""),
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
    date: str
    amount: float
    method: str = "cash"
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Payment":
        return Payment(
            date=data.get("date") or datetime.today().strftime(DATE_FORMAT),
            amount=float(data.get("amount", 0.0) or 0.0),
            method=data.get("method", "cash"),
            note=data.get("note", ""),
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
    contract_type: str = "Storage Only"
    daily_rate: float
    tow_fee: float = 0.0
    impound_fee: float = 0.0
    admin_fee: float = 0.0
    tow_base_fee: float = 0.0
    mileage_included: float = 0.0
    mileage_rate: float = 0.0
    certified_mail_fee_first: float = 0.0
    certified_mail_fee_second: float = 0.0
    extra_labor_minutes: float = 0.0
    labor_rate_per_hour: float = 0.0
    recovery_miles: float = 0.0
    notes: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    payments: List[Payment] = field(default_factory=list)
    fees: List[Fee] = field(default_factory=list)
    notices: List[Notice] = field(default_factory=list)
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
            "daily_rate": self.daily_rate,
            "tow_fee": self.tow_fee,
            "impound_fee": self.impound_fee,
            "admin_fee": self.admin_fee,
            "tow_base_fee": self.tow_base_fee,
            "mileage_included": self.mileage_included,
            "mileage_rate": self.mileage_rate,
            "certified_mail_fee_first": self.certified_mail_fee_first,
            "certified_mail_fee_second": self.certified_mail_fee_second,
            "extra_labor_minutes": self.extra_labor_minutes,
            "labor_rate_per_hour": self.labor_rate_per_hour,
            "recovery_miles": self.recovery_miles,
            "notes": self.notes,
            "attachments": self.attachments,
            "payments": [p.to_dict() for p in self.payments],
            "fees": [f.to_dict() for f in self.fees],
            "notices": [n.to_dict() for n in self.notices],
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
            contract_type=data.get("contract_type", "Storage Only"),
            daily_rate=float(data.get("daily_rate", 0.0) or 0.0),
            tow_fee=float(data.get("tow_fee", 0.0) or 0.0),
            impound_fee=float(data.get("impound_fee", 0.0) or 0.0),
            admin_fee=float(data.get("admin_fee", 0.0) or 0.0),
            tow_base_fee=float(data.get("tow_base_fee", 0.0) or 0.0),
            mileage_included=float(data.get("mileage_included", 0.0) or 0.0),
            mileage_rate=float(data.get("mileage_rate", 0.0) or 0.0),
            certified_mail_fee_first=float(data.get("certified_mail_fee_first", 0.0) or 0.0),
            certified_mail_fee_second=float(data.get("certified_mail_fee_second", 0.0) or 0.0),
            extra_labor_minutes=float(data.get("extra_labor_minutes", 0.0) or 0.0),
            labor_rate_per_hour=float(data.get("labor_rate_per_hour", 0.0) or 0.0),
            recovery_miles=float(data.get("recovery_miles", 0.0) or 0.0),
            notes=list(data.get("notes", [])),
            attachments=list(data.get("attachments", [])),
            payments=[Payment.from_dict(p) for p in data.get("payments", [])],
            fees=[Fee.from_dict(f) for f in data.get("fees", [])],
            notices=[Notice.from_dict(n) for n in data.get("notices", [])],
            status=data.get("status", "Active"),
            first_notice_sent_date=data.get("first_notice_sent_date", ""),
            second_notice_sent_date=data.get("second_notice_sent_date", ""),
            lien_eligible_date=data.get("lien_eligible_date", ""),
        )


@dataclass
class StorageData:
    contracts: List[StorageContract] = field(default_factory=list)
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
