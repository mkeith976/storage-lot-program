"""Tkinter-based storage and impound management GUI with safer prompts."""

from __future__ import annotations

import csv
import json
import math
import os
import sqlite3
import subprocess
from pathlib import Path
from contextlib import closing
from datetime import datetime, timedelta
from typing import Iterable, Optional

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from yard_manager import (
    DATE_FORMAT,
    LIEN_ELIGIBLE_EXTRA_DAYS,
    LIEN_NOTICE_DAYS,
    calc_totals as core_calc_totals,
    generate_invoice_text,
    init_db,
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "yard_manager.db"
FEE_CONFIG_FILE = BASE_DIR / "fees.json"

DEFAULT_FEES = {
    "tow_base": 182.89,
    "daily_storage": 48.77,
    "admin_fee": 60.96,
    "base_miles_included": 10.0,
    "per_mile_rate": 4.88,
    "labor_block_minutes": 15.0,
    "labor_rate": 45.73,
    "storage_monthly": 60.0,
    "storage_daily": 7.0,
    "storage_car_monthly": 60.0,
    "storage_car_daily": 7.0,
    "storage_truck_monthly": 70.0,
    "storage_truck_daily": 8.0,
    "storage_motorcycle_monthly": 40.0,
    "storage_motorcycle_daily": 5.0,
    "storage_rv_monthly": 120.0,
    "storage_rv_daily": 15.0,
    "storage_boat_monthly": 90.0,
    "storage_boat_daily": 10.0,
    "storage_trailer_monthly": 50.0,
    "storage_trailer_daily": 6.0,
}


def get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def add_column_if_missing(cur: sqlite3.Cursor, table: str, col: str, type_def: str) -> None:
    try:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {type_def}")
    except sqlite3.OperationalError:
        pass


def ensure_attachments_table() -> None:
    with closing(get_conn()) as conn, closing(conn.cursor()) as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                impound_id INTEGER,
                contract_id INTEGER,
                path TEXT NOT NULL,
                note TEXT,
                FOREIGN KEY(impound_id) REFERENCES impounds(id),
                FOREIGN KEY(contract_id) REFERENCES storage_contracts(id)
            )
            """
        )
        add_column_if_missing(cur, "attachments", "contract_id", "INTEGER")
        conn.commit()


def ensure_storage_tables() -> None:
    with closing(get_conn()) as conn, closing(conn.cursor()) as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS storage_contracts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate TEXT,
                state TEXT,
                vin TEXT,
                make TEXT,
                model TEXT,
                color TEXT,
                vehicle_type TEXT,
                customer_name TEXT,
                customer_phone TEXT,
                customer_address TEXT,
                location TEXT,
                start_date TEXT,
                billing_type TEXT,
                rate REAL,
                status TEXT,
                next_due_date TEXT,
                lien_notice_date TEXT,
                lien_eligible_date TEXT,
                lien_started_date TEXT,
                sold_date TEXT,
                sale_amount REAL,
                buyer_name TEXT,
                buyer_address TEXT,
                surplus_amount REAL,
                surplus_disposition TEXT,
                cert_mail_fee REAL,
                late_fee_total REAL,
                other_fees_total REAL,
                notes TEXT
            )
            """
        )

        add_column_if_missing(cur, "storage_contracts", "vehicle_type", "TEXT")
        add_column_if_missing(cur, "storage_contracts", "customer_address", "TEXT")
        add_column_if_missing(cur, "storage_contracts", "lien_started_date", "TEXT")
        add_column_if_missing(cur, "storage_contracts", "sold_date", "TEXT")
        add_column_if_missing(cur, "storage_contracts", "sale_amount", "REAL")
        add_column_if_missing(cur, "storage_contracts", "buyer_name", "TEXT")
        add_column_if_missing(cur, "storage_contracts", "buyer_address", "TEXT")
        add_column_if_missing(cur, "storage_contracts", "surplus_amount", "REAL")
        add_column_if_missing(cur, "storage_contracts", "surplus_disposition", "TEXT")
        add_column_if_missing(cur, "storage_contracts", "cert_mail_fee", "REAL")
        add_column_if_missing(cur, "storage_contracts", "late_fee_total", "REAL")
        add_column_if_missing(cur, "storage_contracts", "other_fees_total", "REAL")

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS storage_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_id INTEGER NOT NULL,
                date TEXT,
                amount REAL,
                method TEXT,
                note TEXT,
                FOREIGN KEY(contract_id) REFERENCES storage_contracts(id)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS storage_charges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_id INTEGER NOT NULL,
                date TEXT,
                amount REAL,
                charge_type TEXT,
                description TEXT,
                period_start TEXT,
                period_end TEXT,
                FOREIGN KEY(contract_id) REFERENCES storage_contracts(id)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS storage_notices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_id INTEGER NOT NULL,
                notice_type TEXT,
                date_generated TEXT,
                date_sent TEXT,
                amount_due REAL,
                notes TEXT,
                FOREIGN KEY(contract_id) REFERENCES storage_contracts(id)
            )
            """
        )

        conn.commit()


def load_fees() -> dict[str, float]:
    fees = DEFAULT_FEES.copy()
    if FEE_CONFIG_FILE.exists():
        try:
            with FEE_CONFIG_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in data.items():
                if k in fees and isinstance(v, (int, float)):
                    fees[k] = float(v)
        except Exception:
            pass
    return fees


def save_fees(fees: dict[str, float]) -> None:
    with FEE_CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(fees, f, indent=2)


def validate_date(date_str: str, title: str) -> Optional[str]:
    if not date_str:
        return None
    try:
        datetime.strptime(date_str, DATE_FORMAT)
    except ValueError:
        messagebox.showerror(title, "Invalid date format. Use YYYY-MM-DD.")
        return None
    return date_str


def prompt_date(title: str, prompt: str, default: Optional[str] = None) -> Optional[str]:
    base = default or datetime.today().strftime(DATE_FORMAT)
    value = simpledialog.askstring(title, f"{prompt} [{base}]:") or base
    return validate_date(value, title)


def prompt_choice(title: str, prompt: str, valid: Iterable[str], default: str) -> str:
    value = simpledialog.askstring(title, prompt) or default
    value = value.strip().upper()
    valid_set = {v.upper() for v in valid}
    return value if value in valid_set else default


def prompt_string(title: str, prompt: str, default: str = "") -> str:
    return (simpledialog.askstring(title, prompt) or default).strip()


def prompt_float(title: str, prompt: str, default: float) -> float:
    raw = simpledialog.askstring(title, f"{prompt} [default {default:.2f}]:")
    if raw is None or raw.strip() == "":
        return float(default)
    try:
        return float(raw)
    except ValueError:
        messagebox.showwarning(title, "Invalid number. Using default.")
        return float(default)


def fetch_open_impounds():
    with closing(get_conn()) as conn, closing(conn.cursor()) as cur:
        cur.execute(
            """
            SELECT i.id, v.plate, v.state, v.make, v.model,
                   i.date_in, i.tow_fee, i.daily_storage, i.admin_fee, i.other_fee,
                   i.lien_notice_date, i.lien_eligible_date,
                   i.after_hours_release, i.tarp_used,
                   i.cert_mail_fee, i.lien_process_fee, i.title_assist_fee
            FROM impounds i
            JOIN vehicles v ON v.id = i.vehicle_id
            WHERE i.status = 'IN'
            ORDER BY i.date_in
            """
        )
        return cur.fetchall()


def fetch_released_impounds():
    with closing(get_conn()) as conn, closing(conn.cursor()) as cur:
        cur.execute(
            """
            SELECT i.id, v.plate, v.state, v.make, v.model,
                   i.date_in, i.tow_fee, i.daily_storage, i.admin_fee, i.other_fee,
                   i.lien_notice_date, i.lien_eligible_date,
                   i.after_hours_release, i.tarp_used,
                   i.cert_mail_fee, i.lien_process_fee, i.title_assist_fee,
                   i.date_out
            FROM impounds i
            JOIN vehicles v ON v.id = i.vehicle_id
            WHERE i.status = 'OUT'
            ORDER BY i.date_out DESC, i.date_in DESC
            """
        )
        return cur.fetchall()


def fetch_impound_row(impound_id: int):
    with closing(get_conn()) as conn, closing(conn.cursor()) as cur:
        cur.execute(
            """
            SELECT i.*, v.plate, v.state, v.vin, v.make, v.model, v.color
            FROM impounds i
            JOIN vehicles v ON v.id = i.vehicle_id
            WHERE i.id = ?
            """,
            (impound_id,),
        )
        return cur.fetchone()


def fetch_impound_attachments(impound_id: int):
    with closing(get_conn()) as conn, closing(conn.cursor()) as cur:
        cur.execute(
            """
            SELECT id, path, note
            FROM attachments
            WHERE impound_id = ?
            ORDER BY id
            """,
            (impound_id,),
        )
        return cur.fetchall()


def fetch_storage_charges(contract_id: int):
    with closing(get_conn()) as conn, closing(conn.cursor()) as cur:
        cur.execute(
            """
            SELECT id, date, amount, charge_type, description, period_start, period_end
            FROM storage_charges
            WHERE contract_id = ?
            ORDER BY date, id
            """,
            (contract_id,),
        )
        return cur.fetchall()


def fetch_storage_notices(contract_id: int):
    with closing(get_conn()) as conn, closing(conn.cursor()) as cur:
        cur.execute(
            """
            SELECT id, notice_type, date_generated, date_sent, amount_due, notes
            FROM storage_notices
            WHERE contract_id = ?
            ORDER BY date_generated, id
            """,
            (contract_id,),
        )
        return cur.fetchall()


def get_storage_balance(contract_id: int) -> float:
    with closing(get_conn()) as conn, closing(conn.cursor()) as cur:
        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM storage_charges WHERE contract_id = ?", (contract_id,))
        charges_total = cur.fetchone()[0] or 0.0
        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM storage_payments WHERE contract_id = ?", (contract_id,))
        payments_total = cur.fetchone()[0] or 0.0
    return charges_total - payments_total


class YardGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Yard Manager - GUI")
        self.geometry("1200x550")
        self.fees = load_fees()

        self.tree = ttk.Treeview(
            self,
            columns=("id", "plate", "state", "vehicle", "date_in", "days", "est_total"),
            show="headings",
        )
        for col, label, width in [
            ("id", "ID", 40),
            ("plate", "Plate", 80),
            ("state", "State", 60),
            ("vehicle", "Vehicle", 260),
            ("date_in", "Date In", 90),
            ("days", "Days", 60),
            ("est_total", "Est Total $", 100),
        ]:
            self.tree.heading(col, text=label)
            self.tree.column(col, width=width)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self.on_double_click)

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame, text="Refresh", command=self.refresh).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(btn_frame, text="New Intake", command=self.new_intake).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(btn_frame, text="Release Selected", command=self.release_selected).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(btn_frame, text="Lien Candidates", command=self.show_lien_candidates).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(btn_frame, text="Released Vehicles", command=self.show_released).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(btn_frame, text="Invoice Preview", command=self.invoice_preview).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(btn_frame, text="Storage Contracts", command=self.show_storage_contracts).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(btn_frame, text="Edit Fees", command=self.edit_fees).pack(side=tk.RIGHT, padx=5, pady=5)

        self.refresh()

    def refresh(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)

        try:
            rows = fetch_open_impounds()
        except sqlite3.OperationalError as exc:
            messagebox.showerror("Database Error", str(exc))
            return

        for r in rows:
            totals = core_calc_totals(r)
            vehicle = f"{totals['make']} {totals['model']}"
            self.tree.insert(
                "",
                tk.END,
                values=(
                    totals["id"],
                    totals["plate"],
                    totals["state"],
                    vehicle,
                    totals["date_in"],
                    totals["days"],
                    f"{totals['grand_total']:.2f}",
                ),
            )

    def get_selected_id(self) -> Optional[int]:
        sel = self.tree.selection()
        if not sel:
            return None
        vals = self.tree.item(sel[0], "values")
        return int(vals[0])

    def new_intake(self) -> None:
        choice = prompt_choice(
            "New Intake",
            "Select type:\n\n1 = Tow / Impound\n2 = Storage Customer\n\nEnter 1 or 2:",
            valid=["1", "2"],
            default="1",
        )
        if choice == "2":
            self.new_storage_contract()
        else:
            self.new_impound()

    def new_impound(self) -> None:
        plate = prompt_string("Impound", "Plate:")
        if not plate:
            return
        state = prompt_string("Impound", "State (FL, AL, etc):").upper()
        vin = prompt_string("Impound", "VIN (optional):").upper()
        make = prompt_string("Impound", "Make:")
        model = prompt_string("Impound", "Model:")
        color = prompt_string("Impound", "Color:")

        date_in = prompt_date("Impound", "Date in (YYYY-MM-DD)")
        if not date_in:
            return

        included = self.fees.get("base_miles_included", 10.0)
        per_mile = self.fees.get("per_mile_rate", 0.0)
        miles_str = prompt_string("Mileage", f"Total tow miles (base includes {included:.1f} mi):", str(included))
        try:
            miles = float(miles_str) if miles_str else included
        except ValueError:
            miles = included
        extra_miles = max(0.0, miles - included)
        mileage_fee = extra_miles * per_mile

        block_min = self.fees.get("labor_block_minutes", 15.0) or 15.0
        labor_rate = self.fees.get("labor_rate", 0.0)
        labor_str = prompt_string("Extra Labor", f"Extra labor minutes (billed per {block_min:.0f} min):", "0")
        try:
            minutes = float(labor_str) if labor_str else 0.0
        except ValueError:
            minutes = 0.0
        labor_units = math.ceil(minutes / block_min) if minutes > 0 else 0
        labor_fee = labor_units * labor_rate

        tow_fee = prompt_float("Fees", "Tow base fee $", self.fees["tow_base"])
        daily_storage = prompt_float("Fees", "Daily storage $", self.fees["daily_storage"])
        admin_fee = prompt_float("Fees", "Admin fee $", self.fees["admin_fee"])
        other_fee = mileage_fee + labor_fee

        customer_name = prompt_string("Customer", "Owner / customer name:")
        customer_phone = prompt_string("Customer", "Phone:")
        location = prompt_string("Yard", "Yard / spot:")
        notes = prompt_string("Notes", "Notes (optional):")

        d_in = datetime.strptime(date_in, DATE_FORMAT)
        lien_notice_date = (d_in + timedelta(days=LIEN_NOTICE_DAYS)).strftime(DATE_FORMAT)
        lien_eligible_date = (
            d_in + timedelta(days=LIEN_NOTICE_DAYS + LIEN_ELIGIBLE_EXTRA_DAYS)
        ).strftime(DATE_FORMAT)

        with closing(get_conn()) as conn, closing(conn.cursor()) as cur:
            cur.execute(
                """
                INSERT INTO vehicles (plate, state, vin, make, model, color)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (plate.upper(), state.upper(), vin.upper(), make, model, color),
            )
            vehicle_id = cur.lastrowid

            cur.execute(
                """
                INSERT INTO impounds (
                    vehicle_id, date_in, date_out,
                    tow_fee, daily_storage, admin_fee, other_fee,
                    customer_name, customer_phone, location, status,
                    lien_notice_date, lien_eligible_date, notes,
                    after_hours_release, tarp_used,
                    cert_mail_fee, lien_process_fee, title_assist_fee
                )
                VALUES (?, ?, NULL, ?, ?, ?, ?,
                        ?, ?, ?, 'IN',
                        ?, ?, ?,
                        0, 0,
                        0, 0, 0)
                """,
                (
                    vehicle_id,
                    date_in,
                    tow_fee,
                    daily_storage,
                    admin_fee,
                    other_fee,
                    customer_name,
                    customer_phone,
                    location,
                    lien_notice_date,
                    lien_eligible_date,
                    notes,
                ),
            )
            conn.commit()

        messagebox.showinfo(
            "Saved",
            f"New impound added.\n\nMileage fee: ${mileage_fee:.2f}\nLabor fee: ${labor_fee:.2f}",
        )
        self.refresh()

    def new_storage_contract(self) -> None:
        plate = prompt_string("Storage", "Plate:")
        if not plate:
            return
        state = prompt_string("Storage", "State (FL, AL, etc):").upper()
        vin = prompt_string("Storage", "VIN (optional):").upper()
        make = prompt_string("Storage", "Make:")
        model = prompt_string("Storage", "Model:")
        color = prompt_string("Storage", "Color:")

        vehicle_type = prompt_string(
            "Vehicle Type",
            "Vehicle type (for storage rates):\n\nCAR / TRUCK / MOTORCYCLE / RV / BOAT / TRAILER\n\nType:",
            "CAR",
        ).upper()

        customer_name = prompt_string("Storage", "Customer name:")
        customer_phone = prompt_string("Storage", "Phone:")
        customer_address = prompt_string("Storage", "Mailing address:")
        location = prompt_string("Storage", "Yard / space location:")

        start_date = prompt_date("Storage", "Start date (YYYY-MM-DD)")
        if not start_date:
            return
        d_start = datetime.strptime(start_date, DATE_FORMAT)

        billing_choice = prompt_choice(
            "Billing Type",
            "Billing type:\n\nM = Monthly\nD = Daily\n\nEnter M or D:",
            valid=["M", "D"],
            default="M",
        )
        billing_type = "MONTHLY" if billing_choice == "M" else "DAILY"

        base_key = f"storage_{vehicle_type.lower()}"
        type_key = base_key + ("_monthly" if billing_type == "MONTHLY" else "_daily")
        fallback_key = "storage_monthly" if billing_type == "MONTHLY" else "storage_daily"
        default_rate = self.fees.get(type_key, self.fees.get(fallback_key, 0.0))
        rate = prompt_float(
            "Storage Rate",
            f"Rate $ ({'per month' if billing_type == 'MONTHLY' else 'per day'})",
            default_rate,
        )

        notes_raw = prompt_string("Notes", "Notes (optional):")
        notes = f"[TYPE: {vehicle_type}] {notes_raw}".strip()

        next_due = d_start + timedelta(days=30 if billing_type == "MONTHLY" else 7)
        lien_notice_date = (d_start + timedelta(days=60)).strftime(DATE_FORMAT)
        lien_eligible_date = (d_start + timedelta(days=90)).strftime(DATE_FORMAT)

        with closing(get_conn()) as conn, closing(conn.cursor()) as cur:
            cur.execute(
                """
                INSERT INTO storage_contracts (
                    plate, state, vin, make, model, color, vehicle_type,
                    customer_name, customer_phone, customer_address, location,
                    start_date, billing_type, rate,
                    status, next_due_date,
                    lien_notice_date, lien_eligible_date, lien_started_date,
                    sold_date, sale_amount, buyer_name, buyer_address,
                    surplus_amount, surplus_disposition,
                    cert_mail_fee, late_fee_total, other_fees_total,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?, NULL,
                        NULL, NULL, NULL, NULL,
                        NULL, NULL,
                        0, 0, 0,
                        ?)
                """,
                (
                    plate.upper(),
                    state.upper(),
                    vin.upper(),
                    make,
                    model,
                    color,
                    vehicle_type,
                    customer_name,
                    customer_phone,
                    customer_address,
                    location,
                    start_date,
                    billing_type,
                    rate,
                    next_due.strftime(DATE_FORMAT),
                    lien_notice_date,
                    lien_eligible_date,
                    notes,
                ),
            )
            contract_id = cur.lastrowid

            add_initial = messagebox.askyesno("Initial Charge", "Create an initial storage charge for the first period?")
            if add_initial:
                period_end = d_start + timedelta(days=30 if billing_type == "MONTHLY" else 1)
                cur.execute(
                    """
                    INSERT INTO storage_charges (
                        contract_id, date, amount, charge_type, description, period_start, period_end
                    ) VALUES (?, ?, ?, 'STORAGE', ?, ?, ?)
                    """,
                    (
                        contract_id,
                        start_date,
                        rate,
                        f"Initial {billing_type.lower()} storage",
                        start_date,
                        period_end.strftime(DATE_FORMAT),
                    ),
                )

            conn.commit()

        messagebox.showinfo("Saved", "New storage contract added.")

    def release_selected(self) -> None:
        iid = self.get_selected_id()
        if not iid:
            messagebox.showwarning("No selection", "Select a vehicle first.")
            return

        date_out = prompt_date("Date Out", "Enter release date (YYYY-MM-DD)")
        if not date_out:
            return

        with closing(get_conn()) as conn, closing(conn.cursor()) as cur:
            cur.execute("UPDATE impounds SET date_out = ?, status = 'OUT' WHERE id = ?", (date_out, iid))
            conn.commit()

        messagebox.showinfo("Released", f"Impound {iid} marked as released.")
        self.refresh()

    def invoice_preview(self) -> None:
        iid = self.get_selected_id()
        if not iid:
            messagebox.showwarning("No selection", "Select a vehicle first.")
            return

        with closing(get_conn()) as conn, closing(conn.cursor()) as cur:
            cur.execute(
                """
                SELECT i.id, v.plate, v.state, v.make, v.model,
                       i.date_in, i.tow_fee, i.daily_storage, i.admin_fee, i.other_fee,
                       i.lien_notice_date, i.lien_eligible_date,
                       i.after_hours_release, i.tarp_used,
                       i.cert_mail_fee, i.lien_process_fee, i.title_assist_fee,
                       i.date_out
                FROM impounds i
                JOIN vehicles v ON v.id = i.vehicle_id
                WHERE i.id = ?
                """,
                (iid,),
            )
            row = cur.fetchone()

        if not row:
            messagebox.showerror("Error", "Record not found.")
            return

        base = row[:-1]
        date_out_db = row[-1]
        default_date_out = date_out_db or datetime.today().strftime(DATE_FORMAT)

        date_out = prompt_date("Invoice Preview", "Use date out (YYYY-MM-DD)", default=default_date_out)
        if not date_out:
            return

        totals = core_calc_totals(base, date_out=date_out)
        text = generate_invoice_text(iid, totals, date_out)

        win = tk.Toplevel(self)
        win.title(f"Invoice Preview - ID {iid}")
        txt = tk.Text(win, wrap="word", width=80, height=30)
        txt.pack(fill=tk.BOTH, expand=True)
        txt.insert("1.0", text)
        txt.config(state="disabled")

    def show_lien_candidates(self) -> None:
        rows = fetch_open_impounds()
        candidates = []
        for r in rows:
            totals = core_calc_totals(r)
            if totals["days"] >= LIEN_NOTICE_DAYS:
                candidates.append(totals)

        if not candidates:
            messagebox.showinfo("Lien Candidates", "No vehicles at or over lien threshold.")
            return

        win = tk.Toplevel(self)
        win.title("Lien Candidates")

        tree = ttk.Treeview(
            win,
            columns=("id", "plate", "state", "vehicle", "days", "est_total"),
            show="headings",
        )
        for col, label, width in [
            ("id", "ID", 40),
            ("plate", "Plate", 80),
            ("state", "State", 60),
            ("vehicle", "Vehicle", 220),
            ("days", "Days", 60),
            ("est_total", "Est Total $", 100),
        ]:
            tree.heading(col, text=label)
            tree.column(col, width=width)
        tree.pack(fill=tk.BOTH, expand=True)

        for c in candidates:
            vehicle = f"{c['make']} {c['model']}"
            tree.insert(
                "",
                tk.END,
                values=(c["id"], c["plate"], c["state"], vehicle, c["days"], f"{c['grand_total']:.2f}"),
            )

    def show_released(self) -> None:
        rows = fetch_released_impounds()
        win = tk.Toplevel(self)
        win.title("Released Vehicles")

        tree = ttk.Treeview(
            win,
            columns=("id", "plate", "state", "vehicle", "date_in", "date_out", "total"),
            show="headings",
        )
        for col, label, width in [
            ("id", "ID", 40),
            ("plate", "Plate", 80),
            ("state", "State", 60),
            ("vehicle", "Vehicle", 220),
            ("date_in", "In", 90),
            ("date_out", "Out", 90),
            ("total", "Total $", 100),
        ]:
            tree.heading(col, text=label)
            tree.column(col, width=width)
        tree.pack(fill=tk.BOTH, expand=True)

        for r in rows:
            base = r[:-1]
            date_out = r[-1]
            totals = core_calc_totals(base, date_out=date_out)
            vehicle = f"{totals['make']} {totals['model']}"
            tree.insert(
                "",
                tk.END,
                values=(
                    totals["id"],
                    totals["plate"],
                    totals["state"],
                    vehicle,
                    totals["date_in"],
                    date_out or "",
                    f"{totals['grand_total']:.2f}",
                ),
            )

    def show_storage_contracts(self) -> None:
        win = tk.Toplevel(self)
        win.title("Storage Contracts")

        tree = ttk.Treeview(
            win,
            columns=(
                "id",
                "plate",
                "state",
                "customer",
                "billing",
                "rate",
                "start",
                "next_due",
                "status",
                "late_days",
                "balance",
            ),
            show="headings",
        )
        for col, label, width in [
            ("id", "ID", 40),
            ("plate", "Plate", 80),
            ("state", "State", 60),
            ("customer", "Customer", 180),
            ("billing", "Type", 80),
            ("rate", "Rate $", 70),
            ("start", "Start", 90),
            ("next_due", "Next Due", 90),
            ("status", "Status", 90),
            ("late_days", "Late Days", 80),
            ("balance", "Balance $", 90),
        ]:
            tree.heading(col, text=label)
            tree.column(col, width=width)
        tree.pack(fill=tk.BOTH, expand=True)

        def refresh_list() -> None:
            for item in tree.get_children():
                tree.delete(item)

            with closing(get_conn()) as conn, closing(conn.cursor()) as cur:
                cur.execute(
                    """
                    SELECT id, plate, state, customer_name, billing_type,
                           rate, start_date, next_due_date, status
                    FROM storage_contracts
                    ORDER BY start_date
                    """
                )
                rows = cur.fetchall()

            today = datetime.today()
            for cid, plate, state, customer, btype, rate, start, next_due, status in rows:
                late_days = 0
                flag = status
                if next_due:
                    try:
                        nd = datetime.strptime(next_due, DATE_FORMAT)
                        late_days = max((today - nd).days, 0)
                    except ValueError:
                        late_days = 0
                if late_days > 0 and status == "ACTIVE":
                    flag = "LATE"
                if late_days >= LIEN_NOTICE_DAYS and status not in ("SOLD", "CANCELLED"):
                    flag = "LIEN-CAND"

                balance = get_storage_balance(cid)
                tree.insert(
                    "",
                    tk.END,
                    values=(
                        cid,
                        plate,
                        state,
                        customer,
                        btype,
                        f"{rate:.2f}",
                        start,
                        next_due or "",
                        flag,
                        late_days,
                        f"{balance:.2f}",
                    ),
                )

        def get_selected_contract_id() -> Optional[int]:
            sel = tree.selection()
            if not sel:
                return None
            vals = tree.item(sel[0], "values")
            return int(vals[0])

        def add_payment() -> None:
            cid = get_selected_contract_id()
            if not cid:
                messagebox.showwarning("No selection", "Select a contract first.")
                return

            amount_str = prompt_string("Payment", "Payment amount $:")
            if not amount_str:
                return
            try:
                amount = float(amount_str)
            except ValueError:
                messagebox.showerror("Error", "Invalid amount.")
                return

            date_str = prompt_date("Payment", "Payment date (YYYY-MM-DD)")
            if not date_str:
                return

            method = prompt_string("Payment", "Method (cash/card/etc):")
            note = prompt_string("Payment", "Note (optional):")

            with closing(get_conn()) as conn, closing(conn.cursor()) as cur:
                cur.execute(
                    "INSERT INTO storage_payments (contract_id, date, amount, method, note) VALUES (?, ?, ?, ?, ?)",
                    (cid, date_str, amount, method, note),
                )

                cur.execute("SELECT billing_type, rate, next_due_date FROM storage_contracts WHERE id = ?", (cid,))
                row = cur.fetchone()
                if row:
                    btype, rate_val, next_due = row
                    try:
                        nd = datetime.strptime(next_due, DATE_FORMAT) if next_due else datetime.strptime(date_str, DATE_FORMAT)
                    except Exception:
                        nd = datetime.strptime(date_str, DATE_FORMAT)

                    units = max(int(amount / rate_val), 1) if rate_val and rate_val > 0 else 1
                    nd_new = nd + timedelta(days=(30 if btype == "MONTHLY" else 1) * units)

                    cur.execute(
                        "UPDATE storage_contracts SET next_due_date = ?, status = 'ACTIVE' WHERE id = ?",
                        (nd_new.strftime(DATE_FORMAT), cid),
                    )

                conn.commit()
            refresh_list()

        def export_csv() -> None:
            path = filedialog.asksaveasfilename(
                title="Export storage summary",
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            )
            if not path:
                return

            with closing(get_conn()) as conn, closing(conn.cursor()) as cur:
                cur.execute(
                    """
                    SELECT id, plate, state, customer_name, billing_type,
                           rate, start_date, next_due_date, status
                    FROM storage_contracts
                    ORDER BY start_date
                    """
                )
                rows = cur.fetchall()

            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "ID",
                        "Plate",
                        "State",
                        "Customer",
                        "Billing Type",
                        "Rate",
                        "Start",
                        "Next Due",
                        "Status",
                        "Late Days",
                        "Balance",
                    ]
                )
                today = datetime.today()
                for r in rows:
                    cid, plate, state, customer, btype, rate, start, next_due, status = r
                    late_days = 0
                    if next_due:
                        try:
                            nd = datetime.strptime(next_due, DATE_FORMAT)
                            late_days = max((today - nd).days, 0)
                        except ValueError:
                            late_days = 0
                    balance = get_storage_balance(cid)
                    writer.writerow(
                        [
                            cid,
                            plate,
                            state,
                            customer,
                            btype,
                            f"{rate:.2f}",
                            start,
                            next_due or "",
                            status,
                            late_days,
                            f"{balance:.2f}",
                        ]
                    )

            messagebox.showinfo("Exported", f"CSV saved:\n{path}")

        def show_contract_details(event=None) -> None:  # noqa: ARG001
            cid = get_selected_contract_id()
            if not cid:
                return

            with closing(get_conn()) as conn, closing(conn.cursor()) as cur:
                cur.execute(
                    """
                    SELECT
                        id, plate, state, vin, make, model, color, vehicle_type,
                        customer_name, customer_phone, customer_address, location,
                        start_date, billing_type, rate,
                        status, next_due_date,
                        lien_notice_date, lien_eligible_date, lien_started_date,
                        sold_date, sale_amount, buyer_name, buyer_address,
                        surplus_amount, surplus_disposition,
                        cert_mail_fee, late_fee_total, other_fees_total,
                        notes
                    FROM storage_contracts
                    WHERE id = ?
                    """,
                    (cid,),
                )
                contract = cur.fetchone()

                cur.execute(
                    "SELECT date, amount, method, note FROM storage_payments WHERE contract_id = ? ORDER BY date, id",
                    (cid,),
                )
                payments = cur.fetchall()

            charges = fetch_storage_charges(cid)
            notices = fetch_storage_notices(cid)
            balance = get_storage_balance(cid)

            if not contract:
                messagebox.showerror("Error", "Contract not found.")
                return

            (
                cid2,
                plate,
                state,
                vin,
                make,
                model,
                color,
                vehicle_type,
                cust,
                phone,
                addr,
                loc,
                start,
                btype,
                rate,
                status,
                next_due,
                lien_notice,
                lien_eligible,
                lien_started,
                sold_date,
                sale_amount,
                buyer_name,
                buyer_address,
                surplus_amount,
                surplus_disposition,
                cert_mail_fee,
                late_fee_total,
                other_fees_total,
                notes,
            ) = contract

            win_det = tk.Toplevel(win)
            win_det.title(f"Storage Contract #{cid2}")

            info = [
                ("Plate", f"{plate} {state}"),
                ("VIN", vin),
                ("Vehicle", f"{color} {make} {model}"),
                ("Vehicle Type", vehicle_type or ""),
                ("Customer", cust),
                ("Phone", phone),
                ("Address", addr),
                ("Location", loc),
                ("Start Date", start),
                ("Billing Type", btype),
                ("Rate", f"${rate:.2f}"),
                ("Status", status),
                ("Next Due", next_due or ""),
                ("Lien Notice", lien_notice),
                ("Lien Eligible", lien_eligible),
                ("Lien Started", lien_started or ""),
                ("Sold Date", sold_date or ""),
                ("Sale Amount", f"${sale_amount or 0:.2f}"),
                ("Buyer Name", buyer_name or ""),
                ("Buyer Address", buyer_address or ""),
                ("Surplus Amount", f"${surplus_amount or 0:.2f}"),
                ("Surplus Notes", surplus_disposition or ""),
                ("Cert Mail Fees", f"${cert_mail_fee or 0:.2f}"),
                ("Late Fees Total", f"${late_fee_total or 0:.2f}"),
                ("Other Fees Total", f"${other_fees_total or 0:.2f}"),
                ("Current Balance", f"${balance:.2f}"),
                ("Notes", notes or ""),
            ]

            row_idx = 0
            for label, val in info:
                tk.Label(win_det, text=f"{label}:", anchor="w", width=15).grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)
                tk.Label(win_det, text=val, anchor="w", wraplength=600, justify="left").grid(row=row_idx, column=1, sticky="w", padx=5, pady=2)
                row_idx += 1

            tk.Label(win_det, text="Charges:", font=("Arial", 10, "bold")).grid(row=row_idx, column=0, sticky="w", padx=5, pady=(10, 2))
            row_idx += 1

            charges_tree = ttk.Treeview(
                win_det,
                columns=("id", "date", "amount", "type", "desc", "period"),
                show="headings",
                height=6,
            )
            for col, lbl, width in [
                ("id", "ID", 40),
                ("date", "Date", 90),
                ("amount", "Amount $", 80),
                ("type", "Type", 80),
                ("desc", "Description", 220),
                ("period", "Period", 160),
            ]:
                charges_tree.heading(col, text=lbl)
                charges_tree.column(col, width=width)
            charges_tree.grid(row=row_idx, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
            win_det.rowconfigure(row_idx, weight=1)
            win_det.columnconfigure(1, weight=1)

            def refresh_charges() -> None:
                for item in charges_tree.get_children():
                    charges_tree.delete(item)
                for cidc, d, amt, ctype, desc, ps, pe in fetch_storage_charges(cid2):
                    period = f"{ps or ''} -> {pe or ''}" if (ps or pe) else ""
                    charges_tree.insert("", tk.END, values=(cidc, d, f"{amt:.2f}", ctype, desc or "", period))

            refresh_charges()

            row_idx += 1
            tk.Label(win_det, text="Notices:", font=("Arial", 10, "bold")).grid(row=row_idx, column=0, sticky="w", padx=5, pady=(10, 2))
            row_idx += 1

            notices_tree = ttk.Treeview(
                win_det,
                columns=("id", "type", "generated", "sent", "amount", "notes"),
                show="headings",
                height=4,
            )
            for col, lbl, width in [
                ("id", "ID", 40),
                ("type", "Type", 80),
                ("generated", "Generated", 90),
                ("sent", "Sent", 90),
                ("amount", "Amount Due $", 100),
                ("notes", "Notes", 220),
            ]:
                notices_tree.heading(col, text=lbl)
                notices_tree.column(col, width=width)
            notices_tree.grid(row=row_idx, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

            def refresh_notices() -> None:
                for item in notices_tree.get_children():
                    notices_tree.delete(item)
                for nid, ntype, dg, ds, amt, nt in fetch_storage_notices(cid2):
                    notices_tree.insert("", tk.END, values=(nid, ntype, dg or "", ds or "", f"{amt or 0:.2f}", nt or ""))

            refresh_notices()

            row_idx += 1
            tk.Label(win_det, text="Payments:", font=("Arial", 10, "bold")).grid(row=row_idx, column=0, sticky="w", padx=5, pady=(10, 2))
            row_idx += 1

            pay_tree = ttk.Treeview(win_det, columns=("date", "amount", "method", "note"), show="headings", height=6)
            for col, lbl, width in [("date", "Date", 90), ("amount", "Amount $", 80), ("method", "Method", 80), ("note", "Note", 220)]:
                pay_tree.heading(col, text=lbl)
                pay_tree.column(col, width=width)
            pay_tree.grid(row=row_idx, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
            for d, amt, mth, nt in payments:
                pay_tree.insert("", tk.END, values=(d, f"{amt:.2f}", mth, nt or ""))

            row_idx += 1
            btn_det_frame = tk.Frame(win_det)
            btn_det_frame.grid(row=row_idx, column=0, columnspan=2, sticky="w", padx=5, pady=5)

            def edit_contract_fees() -> None:
                win_fee = tk.Toplevel(win_det)
                win_fee.title("Edit Storage Fees / Status (This Contract)")

                tk.Label(win_fee, text="Billing Type (MONTHLY/DAILY):").grid(row=0, column=0, sticky="w", padx=5, pady=3)
                e_type = tk.Entry(win_fee)
                e_type.grid(row=0, column=1, sticky="w", padx=5, pady=3)
                e_type.insert(0, btype)

                tk.Label(win_fee, text="Rate $:").grid(row=1, column=0, sticky="w", padx=5, pady=3)
                e_rate = tk.Entry(win_fee)
                e_rate.grid(row=1, column=1, sticky="w", padx=5, pady=3)
                e_rate.insert(0, f"{rate:.2f}")

                tk.Label(win_fee, text="Next Due (YYYY-MM-DD):").grid(row=2, column=0, sticky="w", padx=5, pady=3)
                e_due = tk.Entry(win_fee)
                e_due.grid(row=2, column=1, sticky="w", padx=5, pady=3)
                e_due.insert(0, next_due or "")

                tk.Label(win_fee, text="Status:").grid(row=3, column=0, sticky="w", padx=5, pady=3)
                e_status = tk.Entry(win_fee)
                e_status.grid(row=3, column=1, sticky="w", padx=5, pady=3)
                e_status.insert(0, status)

                def save_local_fees() -> None:
                    new_type = e_type.get().strip().upper() or btype
                    if new_type not in ("MONTHLY", "DAILY"):
                        new_type = btype
                    try:
                        new_rate = float(e_rate.get().strip() or rate)
                    except ValueError:
                        new_rate = rate
                    new_due = e_due.get().strip() or next_due or ""
                    new_status = e_status.get().strip().upper() or status

                    with closing(get_conn()) as conn2, closing(conn2.cursor()) as cur2:
                        cur2.execute(
                            """
                            UPDATE storage_contracts
                            SET billing_type = ?, rate = ?, next_due_date = ?, status = ?
                            WHERE id = ?
                            """,
                            (new_type, new_rate, new_due, new_status, cid2),
                        )
                        conn2.commit()

                    messagebox.showinfo("Saved", "Contract fees/settings updated.")
                    win_fee.destroy()
                    refresh_list()

                tk.Button(win_fee, text="Save", command=save_local_fees).grid(row=4, column=0, columnspan=2, pady=10)

            def edit_lien_info() -> None:
                win_lien = tk.Toplevel(win_det)
                win_lien.title("Lien / Sale Info")

                fields = [
                    ("lien_started", "Lien Started (YYYY-MM-DD):", lien_started or ""),
                    ("sold_date", "Sale / Auction Date (YYYY-MM-DD):", sold_date or ""),
                    ("sale_amount", "Sale Amount $:", f"{sale_amount or 0:.2f}"),
                    ("buyer_name", "Buyer Name:", buyer_name or ""),
                    ("buyer_address", "Buyer Address:", buyer_address or ""),
                    ("surplus_amount", "Surplus Amount $:", f"{surplus_amount or 0:.2f}"),
                    ("surplus_disposition", "Surplus Notes:", surplus_disposition or ""),
                ]
                entries: dict[str, tk.Entry] = {}
                r = 0
                for key, label, val in fields:
                    tk.Label(win_lien, text=label, anchor="w").grid(row=r, column=0, sticky="w", padx=5, pady=3)
                    e = tk.Entry(win_lien, width=50)
                    e.grid(row=r, column=1, sticky="w", padx=5, pady=3)
                    e.insert(0, val)
                    entries[key] = e
                    r += 1

                def save_lien() -> None:
                    ls = entries["lien_started"].get().strip() or None
                    sd = entries["sold_date"].get().strip() or None
                    try:
                        sa = float(entries["sale_amount"].get().strip() or 0.0)
                    except ValueError:
                        sa = sale_amount or 0.0
                    bn = entries["buyer_name"].get().strip() or None
                    ba = entries["buyer_address"].get().strip() or None
                    try:
                        spa = float(entries["surplus_amount"].get().strip() or 0.0)
                    except ValueError:
                        spa = surplus_amount or 0.0
                    spd = entries["surplus_disposition"].get().strip() or None

                    with closing(get_conn()) as conn2, closing(conn2.cursor()) as cur2:
                        cur2.execute(
                            """
                            UPDATE storage_contracts
                            SET lien_started_date = ?, sold_date = ?, sale_amount = ?,
                                buyer_name = ?, buyer_address = ?,
                                surplus_amount = ?, surplus_disposition = ?
                            WHERE id = ?
                            """,
                            (ls, sd, sa, bn, ba, spa, spd, cid2),
                        )
                        conn2.commit()

                    messagebox.showinfo("Saved", "Lien / sale info updated.")
                    win_lien.destroy()

                tk.Button(win_lien, text="Save", command=save_lien).grid(row=r, column=0, columnspan=2, pady=10)

            def add_charge() -> None:
                ch_type = prompt_choice(
                    "Charge Type",
                    "Charge type:\n\nSTORAGE / LATE_FEE / CERT_MAIL / OTHER\n\nType:",
                    valid=["STORAGE", "LATE_FEE", "CERT_MAIL", "OTHER"],
                    default="OTHER",
                )

                date_str = prompt_date("Charge", "Charge date (YYYY-MM-DD)")
                if not date_str:
                    return

                amt_str = prompt_string("Charge", "Amount $:")
                if not amt_str:
                    return
                try:
                    amount = float(amt_str)
                except ValueError:
                    messagebox.showerror("Error", "Invalid amount.")
                    return

                desc = prompt_string("Charge", "Description:", ch_type.title())
                period_start = None
                period_end = None
                if ch_type == "STORAGE":
                    ps = prompt_string("Charge", "Storage period start (YYYY-MM-DD, optional):")
                    pe = prompt_string("Charge", "Storage period end (YYYY-MM-DD, optional):")
                    period_start = ps or None
                    period_end = pe or None

                with closing(get_conn()) as conn2, closing(conn2.cursor()) as cur2:
                    cur2.execute(
                        """
                        INSERT INTO storage_charges (
                            contract_id, date, amount, charge_type, description, period_start, period_end
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (cid2, date_str, amount, ch_type, desc, period_start, period_end),
                    )

                    if ch_type == "CERT_MAIL":
                        cur2.execute("UPDATE storage_contracts SET cert_mail_fee = COALESCE(cert_mail_fee,0) + ? WHERE id = ?", (amount, cid2))
                    elif ch_type == "LATE_FEE":
                        cur2.execute("UPDATE storage_contracts SET late_fee_total = COALESCE(late_fee_total,0) + ? WHERE id = ?", (amount, cid2))
                    elif ch_type == "OTHER":
                        cur2.execute("UPDATE storage_contracts SET other_fees_total = COALESCE(other_fees_total,0) + ? WHERE id = ?", (amount, cid2))

                    conn2.commit()

                refresh_charges()
                messagebox.showinfo("Saved", "Charge added.")

            def add_storage_notice() -> None:
                ntype = prompt_string("Notice Type", "Notice type (e.g. 1ST, 2ND, FINAL):", "NOTICE").upper()

                dg = prompt_date("Notice", "Date generated (YYYY-MM-DD)")
                if not dg:
                    return
                ds = prompt_date("Notice", "Date sent (YYYY-MM-DD)", default=dg)
                if not ds:
                    return

                amt_due_str = prompt_string("Notice", "Amount due shown on notice $:", "0")
                try:
                    amt_due = float(amt_due_str)
                except ValueError:
                    amt_due = 0.0

                notes_n = prompt_string("Notice", "Notes (address sent to, etc):")

                add_cert_charge = messagebox.askyesno("Certified Mail Fee", "Add a CERT_MAIL charge for this notice?")
                cert_amt = 0.0
                if add_cert_charge:
                    cert_str = prompt_string("Notice", "Certified mail charge $:", "0")
                    try:
                        cert_amt = float(cert_str)
                    except ValueError:
                        cert_amt = 0.0

                with closing(get_conn()) as conn2, closing(conn2.cursor()) as cur2:
                    cur2.execute(
                        """
                        INSERT INTO storage_notices (
                            contract_id, notice_type, date_generated, date_sent, amount_due, notes
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (cid2, ntype, dg, ds, amt_due, notes_n),
                    )

                    if cert_amt > 0:
                        cur2.execute(
                            """
                            INSERT INTO storage_charges (
                                contract_id, date, amount, charge_type, description, period_start, period_end
                            ) VALUES (?, ?, ?, 'CERT_MAIL', ?, NULL, NULL)
                            """,
                            (cid2, ds, cert_amt, f"{ntype} notice certified mail"),
                        )
                        cur2.execute("UPDATE storage_contracts SET cert_mail_fee = COALESCE(cert_mail_fee,0) + ? WHERE id = ?", (cert_amt, cid2))

                    conn2.commit()

                refresh_notices()
                refresh_charges()
                messagebox.showinfo("Saved", "Notice recorded.")

            def print_contract_record() -> None:
                charges_list = fetch_storage_charges(cid2)
                payments_list = payments
                balance_local = get_storage_balance(cid2)

                lines = [
                    f"Storage Contract #{cid2}",
                    "=" * 50,
                    f"Plate: {plate} {state}",
                    f"VIN: {vin}",
                    f"Vehicle: {vehicle_type or ''} {color} {make} {model}",
                    f"Customer: {cust}",
                    f"Phone: {phone}",
                    f"Address: {addr}",
                    f"Location: {loc}",
                    f"Start Date: {start}",
                    f"Billing: {btype} at ${rate:.2f}",
                    f"Status: {status}",
                    f"Next Due: {next_due or ''}",
                    f"Lien Notice: {lien_notice}",
                    f"Lien Eligible: {lien_eligible}",
                    f"Lien Started: {lien_started or ''}",
                    f"Sold Date: {sold_date or ''}",
                    f"Sale Amount: ${sale_amount or 0:.2f}",
                    f"Buyer: {buyer_name or ''}",
                    f"Buyer Address: {buyer_address or ''}",
                    f"Surplus Amount: ${surplus_amount or 0:.2f}",
                    f"Surplus Notes: {surplus_disposition or ''}",
                    "",
                    f"Cert Mail Fees: ${cert_mail_fee or 0:.2f}",
                    f"Late Fees Total: ${late_fee_total or 0:.2f}",
                    f"Other Fees Total: ${other_fees_total or 0:.2f}",
                    "",
                    "Notes:",
                    notes or "",
                    "",
                    "CHARGES:",
                ]

                total_charges = 0.0
                for cidc, d, amt, ctype, desc, ps, pe in charges_list:
                    total_charges += amt
                    period = f" [{ps or ''} -> {pe or ''}]" if (ps or pe) else ""
                    lines.append(f"  {d}  ${amt:.2f}  {ctype}  {desc or ''}{period}")
                lines.append(f"Total Charges: ${total_charges:.2f}")
                lines.append("")
                lines.append("PAYMENTS:")
                total_pay = 0.0
                for d, amt, mth, nt in payments_list:
                    total_pay += amt
                    lines.append(f"  {d}  ${amt:.2f}  {mth}  {nt or ''}")
                lines.append(f"Total Payments: ${total_pay:.2f}")
                lines.append("")
                lines.append(f"CURRENT BALANCE: ${balance_local:.2f}")

                text = "\n".join(lines)

                win_txt = tk.Toplevel(win_det)
                win_txt.title(f"Print Preview - Contract #{cid2}")
                txt = tk.Text(win_txt, wrap="word", width=90, height=35)
                txt.pack(fill=tk.BOTH, expand=True)
                txt.insert("1.0", text)

                def save_to_file() -> None:
                    out_path = filedialog.asksaveasfilename(
                        title="Save record as text",
                        defaultextension=".txt",
                        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
                    )
                    if not out_path:
                        return
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(text)
                    messagebox.showinfo("Saved", f"Record saved:\n{out_path}")

                tk.Button(win_txt, text="Save As Text", command=save_to_file).pack(pady=5)

            tk.Button(btn_det_frame, text="Edit Storage Fees", command=edit_contract_fees).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_det_frame, text="Lien Info", command=edit_lien_info).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_det_frame, text="Add Charge", command=add_charge).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_det_frame, text="Add Storage Notice", command=add_storage_notice).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_det_frame, text="Print Record", command=print_contract_record).pack(side=tk.LEFT, padx=5)

        def edit_storage_defaults() -> None:
            win_fee = tk.Toplevel(win)
            win_fee.title("Edit Storage Default Fees")

            fields = [
                ("storage_monthly", "DEFAULT monthly $"),
                ("storage_daily", "DEFAULT daily $"),
                ("storage_car_monthly", "CAR monthly $"),
                ("storage_car_daily", "CAR daily $"),
                ("storage_truck_monthly", "TRUCK monthly $"),
                ("storage_truck_daily", "TRUCK daily $"),
                ("storage_motorcycle_monthly", "MOTORCYCLE monthly $"),
                ("storage_motorcycle_daily", "MOTORCYCLE daily $"),
                ("storage_rv_monthly", "RV monthly $"),
                ("storage_rv_daily", "RV daily $"),
                ("storage_boat_monthly", "BOAT monthly $"),
                ("storage_boat_daily", "BOAT daily $"),
                ("storage_trailer_monthly", "TRAILER monthly $"),
                ("storage_trailer_daily", "TRAILER daily $"),
            ]

            entries: dict[str, tk.Entry] = {}
            row = 0
            for key, label in fields:
                tk.Label(win_fee, text=label + ":", anchor="w").grid(row=row, column=0, sticky="w", padx=5, pady=3)
                e = tk.Entry(win_fee)
                e.grid(row=row, column=1, sticky="w", padx=5, pady=3)
                val = self.fees.get(key, DEFAULT_FEES.get(key, 0.0))
                e.insert(0, f"{val:.2f}")
                entries[key] = e
                row += 1

            def save_defaults() -> None:
                for key, entry in entries.items():
                    txt_val = entry.get().strip()
                    try:
                        val = float(txt_val)
                        self.fees[key] = val
                    except ValueError:
                        continue
                save_fees(self.fees)
                messagebox.showinfo("Saved", "Storage default fees updated.")
                win_fee.destroy()

            tk.Button(win_fee, text="Save", command=save_defaults).grid(row=row, column=0, columnspan=2, pady=10)

        btn_frame = tk.Frame(win)
        btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame, text="Add Payment", command=add_payment).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(btn_frame, text="Edit Storage Defaults", command=edit_storage_defaults).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(btn_frame, text="Export CSV", command=export_csv).pack(side=tk.LEFT, padx=5, pady=5)

        tree.bind("<Double-1>", lambda e: show_contract_details())
        refresh_list()

    def edit_fees(self) -> None:
        win = tk.Toplevel(self)
        win.title("Edit Tow / Impound Fee Defaults")

        labels = {
            "tow_base": "Tow base $",
            "daily_storage": "Daily storage (impound) $",
            "admin_fee": "Admin fee $",
            "base_miles_included": "Included miles",
            "per_mile_rate": "Per-mile after base $",
            "labor_block_minutes": "Labor block minutes",
            "labor_rate": "Labor rate per block $",
        }
        entries: dict[str, tk.Entry] = {}

        row = 0
        for key in [
            "tow_base",
            "daily_storage",
            "admin_fee",
            "base_miles_included",
            "per_mile_rate",
            "labor_block_minutes",
            "labor_rate",
        ]:
            tk.Label(win, text=labels[key] + ":", anchor="w").grid(row=row, column=0, sticky="w", padx=5, pady=3)
            e = tk.Entry(win)
            e.grid(row=row, column=1, sticky="w", padx=5, pady=3)
            e.insert(0, f"{self.fees[key]:.2f}")
            entries[key] = e
            row += 1

        def save() -> None:
            for key, entry in entries.items():
                txt = entry.get().strip()
                try:
                    val = float(txt)
                    self.fees[key] = val
                except ValueError:
                    continue
            save_fees(self.fees)
            messagebox.showinfo("Saved", "Tow/impound fee defaults updated.")
            win.destroy()

        tk.Button(win, text="Save", command=save).grid(row=row, column=0, columnspan=2, pady=10)

    def on_double_click(self, event: tk.Event) -> None:
        item = self.tree.identify_row(event.y)
        if not item:
            return
        vals = self.tree.item(item, "values")
        if not vals:
            return
        impound_id = int(vals[0])
        self.show_details(impound_id)

    def show_details(self, impound_id: int) -> None:
        row = fetch_impound_row(impound_id)
        if not row:
            messagebox.showerror("Error", "Record not found.")
            return

        (
            imp_id,
            vehicle_id,
            date_in,
            date_out,
            tow_fee,
            daily_storage,
            admin_fee,
            other_fee,
            customer_name,
            customer_phone,
            location,
            status,
            lien_notice_date,
            lien_eligible_date,
            notes,
            after_hours_release,
            tarp_used,
            cert_mail_fee,
            lien_process_fee,
            title_assist_fee,
            plate,
            state,
            vin,
            make,
            model,
            color,
        ) = row

        details_win = tk.Toplevel(self)
        details_win.title(f"Details - ID {imp_id}")

        info = [
            ("Status", status),
            ("Plate", f"{plate} {state}"),
            ("VIN", vin),
            ("Vehicle", f"{color} {make} {model}"),
            ("Customer", customer_name),
            ("Phone", customer_phone),
            ("Location", location),
            ("Date In", date_in),
            ("Date Out", date_out or ""),
            ("Lien Notice", lien_notice_date),
            ("Lien Eligible", lien_eligible_date),
            ("Tow Fee", f"${tow_fee:.2f}"),
            ("Daily Storage", f"${daily_storage:.2f}"),
            ("Admin Fee", f"${admin_fee:.2f}"),
            ("Other Fees", f"${other_fee:.2f}"),
            ("After Hours", "Yes" if after_hours_release else "No"),
            ("Tarp Used", "Yes" if tarp_used else "No"),
            ("Cert Mail", f"${(cert_mail_fee or 0):.2f}"),
            ("Lien Proc", f"${(lien_process_fee or 0):.2f}"),
            ("Title Assist", f"${(title_assist_fee or 0):.2f}"),
            ("Notes", notes or ""),
        ]

        row_idx = 0
        for label, value in info:
            tk.Label(details_win, text=f"{label}:", anchor="w", width=15).grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)
            tk.Label(details_win, text=value, anchor="w").grid(row=row_idx, column=1, sticky="w", padx=5, pady=2)
            row_idx += 1

        tk.Label(details_win, text="Attachments:", font=("Arial", 10, "bold")).grid(row=row_idx, column=0, sticky="w", padx=5, pady=(10, 2))
        row_idx += 1

        attach_frame = tk.Frame(details_win)
        attach_frame.grid(row=row_idx, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        details_win.rowconfigure(row_idx, weight=1)
        details_win.columnconfigure(1, weight=1)

        attach_tree = ttk.Treeview(attach_frame, columns=("id", "path", "note"), show="headings", height=5)
        for col, label, width in [("id", "ID", 40), ("path", "Path", 300), ("note", "Note", 150)]:
            attach_tree.heading(col, text=label)
            attach_tree.column(col, width=width)
        attach_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(attach_frame, orient="vertical", command=attach_tree.yview)
        attach_tree.configure(yscroll=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        btn_attach_frame = tk.Frame(details_win)
        btn_attach_frame.grid(row=row_idx + 1, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        def refresh_attachments() -> None:
            for item in attach_tree.get_children():
                attach_tree.delete(item)
            for aid, path, note_a in fetch_impound_attachments(imp_id):
                attach_tree.insert("", tk.END, values=(aid, path, note_a or ""))

        def add_attachment() -> None:
            file_path = filedialog.askopenfilename(title="Select attachment (photo or document)")
            if not file_path:
                return
            note_a = simpledialog.askstring("Attachment Note", "Note/description (optional):") or ""
            with closing(get_conn()) as conn2, closing(conn2.cursor()) as cur2:
                cur2.execute(
                    "INSERT INTO attachments (impound_id, contract_id, path, note) VALUES (?, ?, ?, ?)",
                    (imp_id, None, file_path, note_a),
                )
                conn2.commit()
            refresh_attachments()

        def open_attachment() -> None:
            sel = attach_tree.selection()
            if not sel:
                messagebox.showwarning("No selection", "Select an attachment first.")
                return
            vals_local = attach_tree.item(sel[0], "values")
            path_local = vals_local[1]
            if not os.path.exists(path_local):
                messagebox.showerror("Missing file", f"File not found:\n{path_local}")
                return
            try:
                subprocess.Popen(["xdg-open", path_local])
            except Exception as exc:
                messagebox.showerror("Error", f"Could not open file:\n{exc}")

        tk.Button(btn_attach_frame, text="Add Attachment", command=add_attachment).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_attach_frame, text="Open Attachment", command=open_attachment).pack(side=tk.LEFT, padx=5)
        refresh_attachments()

        extra_frame = tk.Frame(details_win)
        extra_frame.grid(row=row_idx + 2, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        def edit_extra_fees() -> None:
            with closing(get_conn()) as conn_local, closing(conn_local.cursor()) as cur_local:
                cur_local.execute(
                    "SELECT other_fee, cert_mail_fee, lien_process_fee, title_assist_fee FROM impounds WHERE id = ?",
                    (imp_id,),
                )
                row2 = cur_local.fetchone()

            if not row2:
                messagebox.showerror("Error", "Record not found.")
                return
            o_fee, c_fee, l_fee, t_fee = [x or 0.0 for x in row2]

            win_fee = tk.Toplevel(details_win)
            win_fee.title("Edit Extra Fees")

            labels_local = [
                ("other", "Other fees $", o_fee),
                ("cert", "Certified mail total $", c_fee),
                ("lien", "Lien processing $", l_fee),
                ("title", "Title assist $", t_fee),
            ]
            entries_local: dict[str, tk.Entry] = {}
            r_local = 0
            for key, lbl, val in labels_local:
                tk.Label(win_fee, text=lbl + ":", anchor="w").grid(row=r_local, column=0, sticky="w", padx=5, pady=3)
                e_local = tk.Entry(win_fee)
                e_local.grid(row=r_local, column=1, sticky="w", padx=5, pady=3)
                e_local.insert(0, f"{val:.2f}")
                entries_local[key] = e_local
                r_local += 1

            def save_local() -> None:
                try:
                    new_other = float(entries_local["other"].get().strip() or o_fee)
                except ValueError:
                    new_other = o_fee
                try:
                    new_cert = float(entries_local["cert"].get().strip() or c_fee)
                except ValueError:
                    new_cert = c_fee
                try:
                    new_lien = float(entries_local["lien"].get().strip() or l_fee)
                except ValueError:
                    new_lien = l_fee
                try:
                    new_title = float(entries_local["title"].get().strip() or t_fee)
                except ValueError:
                    new_title = t_fee

                with closing(get_conn()) as conn2, closing(conn2.cursor()) as cur2:
                    cur2.execute(
                        """
                        UPDATE impounds
                        SET other_fee = ?, cert_mail_fee = ?, lien_process_fee = ?, title_assist_fee = ?
                        WHERE id = ?
                        """,
                        (new_other, new_cert, new_lien, new_title, imp_id),
                    )
                    conn2.commit()
                messagebox.showinfo("Saved", "Extra fees updated.")
                win_fee.destroy()

            tk.Button(win_fee, text="Save", command=save_local).grid(row=r_local, column=0, columnspan=2, pady=10)

        def add_cert_notice() -> None:
            kind = prompt_string("Certified Notice", "Notice type (e.g. 1st, 2nd, Final):", "Notice")
            date_s = prompt_date("Certified Notice", "Date sent (YYYY-MM-DD)")
            if not date_s:
                return
            amt_s = prompt_string("Certified Notice", "Charge for this letter $:", "0")
            try:
                amt = float(amt_s)
            except ValueError:
                amt = 0.0

            with closing(get_conn()) as conn2, closing(conn2.cursor()) as cur2:
                cur2.execute("SELECT cert_mail_fee, notes FROM impounds WHERE id = ?", (imp_id,))
                row2 = cur2.fetchone()
                c_old, notes_old = row2 if row2 else (0.0, notes or "")
                c_old = c_old or 0.0
                new_cert = c_old + amt
                new_notes = (notes_old or "") + f"\nCERT {kind} sent {date_s} ${amt:.2f}"

                cur2.execute("UPDATE impounds SET cert_mail_fee = ?, notes = ? WHERE id = ?", (new_cert, new_notes, imp_id))
                conn2.commit()

            messagebox.showinfo("Saved", f"Certified notice added.\nNew cert mail total: ${new_cert:.2f}")

        def print_impound_record() -> None:
            lines = [
                f"Impound Record ID {imp_id}",
                "=" * 40,
                f"Plate: {plate} {state}",
                f"VIN: {vin}",
                f"Vehicle: {color} {make} {model}",
                f"Customer: {customer_name}",
                f"Phone: {customer_phone}",
                f"Location: {location}",
                f"Status: {status}",
                f"Date In: {date_in}",
                f"Date Out: {date_out or ''}",
                f"Lien Notice: {lien_notice_date}",
                f"Lien Eligible: {lien_eligible_date}",
                "",
                f"Tow Fee: ${tow_fee:.2f}",
                f"Daily Storage: ${daily_storage:.2f}",
                f"Admin Fee: ${admin_fee:.2f}",
                f"Other Fees: ${other_fee:.2f}",
                f"Cert Mail: ${cert_mail_fee or 0:.2f}",
                f"Lien Process: ${lien_process_fee or 0:.2f}",
                f"Title Assist: ${title_assist_fee or 0:.2f}",
                "",
                "Notes:",
                notes or "",
            ]
            text = "\n".join(lines)

            win_txt = tk.Toplevel(details_win)
            win_txt.title(f"Print Preview - Impound {imp_id}")
            txt = tk.Text(win_txt, wrap="word", width=80, height=30)
            txt.pack(fill=tk.BOTH, expand=True)
            txt.insert("1.0", text)

            def save_to_file() -> None:
                out_path = filedialog.asksaveasfilename(
                    title="Save record as text",
                    defaultextension=".txt",
                    filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
                )
                if not out_path:
                    return
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(text)
                messagebox.showinfo("Saved", f"Record saved:\n{out_path}")

            tk.Button(win_txt, text="Save As Text", command=save_to_file).pack(pady=5)

        tk.Button(extra_frame, text="Edit Extra Fees", command=edit_extra_fees).pack(side=tk.LEFT, padx=5)
        tk.Button(extra_frame, text="Add Certified Notice", command=add_cert_notice).pack(side=tk.LEFT, padx=5)
        tk.Button(extra_frame, text="Print Record", command=print_impound_record).pack(side=tk.LEFT, padx=5)


if __name__ == "__main__":
    init_db()
    ensure_attachments_table()
    ensure_storage_tables()
    app = YardGUI()
    app.mainloop()

Add initial yard GUI app
