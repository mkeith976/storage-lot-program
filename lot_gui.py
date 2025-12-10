"""Tkinter UI for the Storage & Recovery Lot program."""
from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from lot_logic import (
    add_notice,
    balance,
    build_contract,
    default_fee_schedule,
    format_contract_record,
    lien_eligibility,
    balance,
    build_contract,
    default_fee_schedule,
    format_contract_summary,
    add_notice,
    lien_timeline,
    load_data,
    load_fee_templates,
    past_due_status,
    record_payment,
    save_data,
    save_fee_templates,
    storage_days,
    storage_days,
    save_data,
    save_fee_templates,
)
from lot_models import Customer, Vehicle, StorageContract, StorageData, DATE_FORMAT


class LotApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Storage & Recovery Lot")
        self.geometry("1200x700")
        self.storage_data: StorageData = load_data()
        self.fee_templates: Dict[str, Dict[str, float]] = load_fee_templates()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.contract_tab = ttk.Frame(self.notebook)
        self.intake_tab = ttk.Frame(self.notebook)
        self.fee_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.contract_tab, text="Contracts")
        self.notebook.add(self.intake_tab, text="Intake")
        self.notebook.add(self.fee_tab, text="Fee Templates")

        self._build_contract_tab()
        self._build_intake_tab()
        self._build_fee_tab()

        self.refresh_contracts()

    # ------------------------------------------------------------------
    # Contracts tab
    # ------------------------------------------------------------------
    def _build_contract_tab(self) -> None:
        container = ttk.Frame(self.contract_tab)
        container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.contract_tree = ttk.Treeview(
            container,
            columns=("id", "customer", "vehicle", "type", "start", "balance", "status"),
            columns=("id", "customer", "vehicle", "start", "balance", "status"),
            show="headings",
            height=12,
        )
        for col, text, width in [
            ("id", "ID", 50),
            ("customer", "Customer", 180),
            ("vehicle", "Vehicle", 180),
            ("type", "Contract Type", 130),
            ("customer", "Customer", 200),
            ("vehicle", "Vehicle", 200),
            ("start", "Start", 90),
            ("balance", "Balance", 90),
            ("status", "Status", 80),
        ]:
            self.contract_tree.heading(col, text=text)
            self.contract_tree.column(col, width=width)
        self.contract_tree.bind("<<TreeviewSelect>>", lambda *_: self._show_selected_contract())
        self.contract_tree.pack(fill=tk.X, pady=(0, 8))

        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_contracts).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Record Payment", command=self._record_payment_dialog).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Add Note", command=self._add_note_dialog).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Generate Notice", command=self._add_notice_dialog).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Print Record", command=self._print_record).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_frame, text="Export Summary", command=self._export_summary).pack(side=tk.RIGHT, padx=4)

        detail = ttk.LabelFrame(container, text="Contract Details")
        detail.pack(fill=tk.BOTH, expand=True)

        self.summary_text = tk.Text(detail, height=16, wrap="word")
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.summary_text.configure(state="disabled")

        timeline_frame = ttk.Frame(detail)
        timeline_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        self.first_notice_var = tk.StringVar()
        self.second_notice_var = tk.StringVar()
        self.lien_var = tk.StringVar()
        self.lien_status_var = tk.StringVar()
        ttk.Label(timeline_frame, textvariable=self.first_notice_var).pack(side=tk.LEFT, padx=4)
        ttk.Label(timeline_frame, textvariable=self.second_notice_var).pack(side=tk.LEFT, padx=4)
        ttk.Label(timeline_frame, textvariable=self.lien_var).pack(side=tk.LEFT, padx=4)
        ttk.Label(timeline_frame, textvariable=self.lien_status_var, foreground="blue").pack(side=tk.LEFT, padx=4)
        ttk.Label(timeline_frame, textvariable=self.first_notice_var).pack(side=tk.LEFT, padx=4)
        ttk.Label(timeline_frame, textvariable=self.second_notice_var).pack(side=tk.LEFT, padx=4)
        ttk.Label(timeline_frame, textvariable=self.lien_var).pack(side=tk.LEFT, padx=4)

    def refresh_contracts(self) -> None:
        for row in self.contract_tree.get_children():
            self.contract_tree.delete(row)

        for contract in self.storage_data.contracts:
            bal = balance(contract)
            vehicle = f"{contract.vehicle.vehicle_type} {contract.vehicle.plate}"
            self.contract_tree.insert(
                "",
                tk.END,
                iid=str(contract.contract_id),
                values=(
                    contract.contract_id,
                    contract.customer.name,
                    vehicle,
                    contract.contract_type,
                    contract.start_date,
                    f"${bal:.2f}",
                    contract.status,
                ),
            )
        self._show_selected_contract()

    def _get_selected_contract(self) -> Optional[StorageContract]:
        sel = self.contract_tree.selection()
        if not sel:
            return None
        contract_id = int(sel[0])
        for contract in self.storage_data.contracts:
            if contract.contract_id == contract_id:
                return contract
        return None

    def _show_selected_contract(self) -> None:
        contract = self._get_selected_contract()
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", tk.END)
        if not contract:
            self.summary_text.insert("1.0", "Select a contract to see details.")
            self.summary_text.configure(state="disabled")
            return

        summary = format_contract_record(contract)
        summary = format_contract_summary(contract)
        self.summary_text.insert("1.0", summary)
        self.summary_text.configure(state="disabled")

        timeline = lien_timeline(contract)
        past_due, days_past_due = past_due_status(contract)
        total_days = storage_days(contract)
        status_text = "Past due" if past_due else "Current"
        first_notice, second_notice, lien_eligible, lien_status = lien_eligibility(contract)
        self.first_notice_var.set(f"1st Notice: {first_notice}")
        self.second_notice_var.set(f"2nd Notice: {second_notice}")
        self.first_notice_var.set(f"1st Notice: {timeline['first_notice']}")
        self.second_notice_var.set(f"2nd Notice: {timeline['second_notice']}")
        suffix = f"{total_days} days since intake"
        if past_due:
            suffix += f" | {days_past_due} days past due"
        self.lien_var.set(f"Earliest lien: {timeline['earliest_lien']} | {status_text} ({suffix})")
        self.lien_status_var.set(f"Lien status: {lien_status} (eligible {lien_eligible})")

    def _record_payment_dialog(self) -> None:
        contract = self._get_selected_contract()
        if not contract:
            messagebox.showwarning("Payment", "Select a contract first.")
            return
        amount_str = simpledialog.askstring("Payment", "Amount received:")
        if not amount_str:
            return
        try:
            amount = float(amount_str)
        except ValueError:
            messagebox.showerror("Payment", "Invalid amount")
            return
        method = simpledialog.askstring("Payment", "Method (cash/card/check):", initialvalue="cash") or "cash"
        note = simpledialog.askstring("Payment", "Note (optional):", initialvalue="") or ""
        record_payment(contract, amount, method, note)
        save_data(self.storage_data)
        self.refresh_contracts()

    def _add_note_dialog(self) -> None:
        contract = self._get_selected_contract()
        if not contract:
            messagebox.showwarning("Notes", "Select a contract first.")
            return
        note = simpledialog.askstring("Note", "Add note/attachment placeholder:")
        if not note:
            return
        contract.notes.append(note)
        save_data(self.storage_data)
        self._show_selected_contract()

    def _add_notice_dialog(self) -> None:
        contract = self._get_selected_contract()
        if not contract:
            messagebox.showwarning("Notices", "Select a contract first.")
            return
        amount_due = balance(contract)
        notice_type = simpledialog.askstring("Notice", "Notice type (1st/2nd/lien)", initialvalue="1st") or "1st"
        add_notice(contract, notice_type, amount_due)
        today = datetime.today().strftime(DATE_FORMAT)
        lower_type = notice_type.lower()
        if "1" in lower_type or "first" in lower_type:
            contract.first_notice_sent_date = today
        elif "2" in lower_type or "second" in lower_type:
            contract.second_notice_sent_date = today
        save_data(self.storage_data)
        self._show_selected_contract()

    def _print_record(self) -> None:
        contract = self._get_selected_contract()
        if not contract:
            messagebox.showwarning("Print Record", "Select a contract first.")
            return
        summary = format_contract_record(contract)
        win = tk.Toplevel(self)
        win.title(f"Contract {contract.contract_id} Print Record")
        save_data(self.storage_data)
        self._show_selected_contract()

    def _export_summary(self) -> None:
        contract = self._get_selected_contract()
        if not contract:
            messagebox.showwarning("Export", "Select a contract first.")
            return
        summary = format_contract_summary(contract)
        win = tk.Toplevel(self)
        win.title(f"Contract {contract.contract_id} Summary")
        txt = tk.Text(win, wrap="word")
        txt.pack(fill=tk.BOTH, expand=True)
        txt.insert("1.0", summary)
        ttk.Button(win, text="Save to file", command=lambda: self._save_summary_to_file(summary)).pack(pady=4)

    def _save_summary_to_file(self, content: str) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if not path:
            return
        Path(path).write_text(content, encoding="utf-8")
        messagebox.showinfo("Print Record", f"Saved to {path}")
        messagebox.showinfo("Export", f"Saved to {path}")

    # ------------------------------------------------------------------
    # Intake tab
    # ------------------------------------------------------------------
    def _build_intake_tab(self) -> None:
        frame = ttk.Frame(self.intake_tab, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        contract_type_frame = ttk.Frame(frame)
        contract_type_frame.pack(fill=tk.X, pady=4)
        ttk.Label(contract_type_frame, text="Contract Type", width=20).pack(side=tk.LEFT)
        self.contract_type = tk.StringVar(value="Storage Only")
        ttk.Combobox(
            contract_type_frame,
            textvariable=self.contract_type,
            values=["Storage Only", "Tow & Recovery"],
            state="readonly",
        ).pack(side=tk.LEFT, padx=4)
        self.contract_type.trace_add("write", lambda *_: self._load_defaults_for_type())

        # Customer
        cust = ttk.LabelFrame(frame, text="Customer")
        cust.pack(fill=tk.X, pady=4)
        self.cust_name = tk.StringVar()
        self.cust_phone = tk.StringVar()
        self.cust_address = tk.StringVar()
        self._add_labeled_entry(cust, "Name", self.cust_name)
        self._add_labeled_entry(cust, "Phone", self.cust_phone)
        self._add_labeled_entry(cust, "Address", self.cust_address, width=50)

        # Vehicle
        veh = ttk.LabelFrame(frame, text="Vehicle")
        veh.pack(fill=tk.X, pady=4)
        self.plate = tk.StringVar()
        self.vin = tk.StringVar()
        self.vehicle_type = tk.StringVar(value="Car")
        self.make = tk.StringVar()
        self.model = tk.StringVar()
        self.color = tk.StringVar()
        self.initial_mileage = tk.StringVar(value="0")
        self.recovery_miles = tk.StringVar(value="0")
        self.extra_labor = tk.StringVar(value="0")
        self.labor_rate = tk.StringVar(value="45")

        self._add_labeled_entry(veh, "Plate", self.plate)
        self._add_labeled_entry(veh, "VIN", self.vin)
        self._add_labeled_entry(veh, "Make", self.make)
        self._add_labeled_entry(veh, "Model", self.model)
        self._add_labeled_entry(veh, "Color", self.color)

        row = ttk.Frame(veh)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Vehicle Type", width=15).pack(side=tk.LEFT)
        type_box = ttk.Combobox(row, textvariable=self.vehicle_type, values=list(self.fee_templates.keys()))
        type_box.pack(side=tk.LEFT, padx=4)
        type_box.bind("<<ComboboxSelected>>", lambda *_: self._load_defaults_for_type())
        ttk.Label(row, text="Initial Mileage").pack(side=tk.LEFT, padx=4)
        ttk.Entry(row, textvariable=self.initial_mileage, width=10).pack(side=tk.LEFT)
        ttk.Label(row, text="Tow Miles", width=12).pack(side=tk.LEFT, padx=4)
        ttk.Entry(row, textvariable=self.recovery_miles, width=10).pack(side=tk.LEFT)
        ttk.Label(row, text="Extra Labor Minutes").pack(side=tk.LEFT, padx=4)
        ttk.Entry(row, textvariable=self.extra_labor, width=10).pack(side=tk.LEFT)
        ttk.Label(row, text="Labor Rate/hr").pack(side=tk.LEFT, padx=4)
        ttk.Entry(row, textvariable=self.labor_rate, width=10).pack(side=tk.LEFT)

        # Contract
        contract_frame = ttk.LabelFrame(frame, text="Storage Contract")
        contract_frame.pack(fill=tk.X, pady=4)
        self.daily_rate = tk.StringVar(value="35")
        self.tow_fee = tk.StringVar(value="150")
        self.impound_fee = tk.StringVar(value="75")
        self.admin_fee = tk.StringVar(value="25")
        self.start_date = tk.StringVar(value=datetime.today().strftime(DATE_FORMAT))
        self.tow_base_fee = tk.StringVar(value="0")
        self.mileage_included = tk.StringVar(value="0")
        self.mileage_rate = tk.StringVar(value="0")
        self.certified_mail_first = tk.StringVar(value="0")
        self.certified_mail_second = tk.StringVar(value="0")

        self._add_labeled_entry(contract_frame, "Start Date (YYYY-MM-DD)", self.start_date)
        self._add_labeled_entry(contract_frame, "Daily Storage Rate", self.daily_rate)
        self._add_labeled_entry(contract_frame, "Tow Fee", self.tow_fee)
        self._add_labeled_entry(contract_frame, "Impound Fee", self.impound_fee)
        self._add_labeled_entry(contract_frame, "Admin Fee", self.admin_fee)
        self._add_labeled_entry(contract_frame, "Tow Base Fee", self.tow_base_fee)
        self._add_labeled_entry(contract_frame, "Mileage Included", self.mileage_included)
        self._add_labeled_entry(contract_frame, "Mileage Rate", self.mileage_rate)
        self._add_labeled_entry(contract_frame, "Certified Mail (1st)", self.certified_mail_first)
        self._add_labeled_entry(contract_frame, "Certified Mail (2nd)", self.certified_mail_second)

        ttk.Button(frame, text="Create Contract", command=self._create_contract).pack(pady=8)
        self._load_defaults_for_type()

        ttk.Button(frame, text="Create Contract", command=self._create_contract).pack(pady=8)

    def _load_defaults_for_type(self) -> None:
        schedule = self.fee_templates.get(self.vehicle_type.get(), default_fee_schedule("Car"))
        self.daily_rate.set(f"{schedule['daily_rate']}")
        self.tow_fee.set(f"{schedule['tow_fee']}")
        self.impound_fee.set(f"{schedule['impound_fee']}")
        self.admin_fee.set(f"{schedule['admin_fee']}")
        if self.contract_type.get() == "Storage Only":
            self.tow_base_fee.set("0")
            self.mileage_included.set("0")
            self.mileage_rate.set("0")
            self.certified_mail_first.set("0")
            self.certified_mail_second.set("0")
        else:
            self.tow_base_fee.set(f"{schedule.get('tow_base_fee', 0.0)}")
            self.mileage_included.set(f"{schedule.get('mileage_included', 0.0)}")
            self.mileage_rate.set(f"{schedule.get('mileage_rate', 0.0)}")
            self.certified_mail_first.set(f"{schedule.get('certified_mail_fee_first', 0.0)}")
            self.certified_mail_second.set(f"{schedule.get('certified_mail_fee_second', 0.0)}")
        self.labor_rate.set(f"{schedule.get('labor_rate', self.labor_rate.get())}")

    def _create_contract(self) -> None:
        try:
            daily_rate = float(self.daily_rate.get())
            tow_fee = float(self.tow_fee.get())
            impound_fee = float(self.impound_fee.get())
            admin_fee = float(self.admin_fee.get())
            labor_minutes = float(self.extra_labor.get())
            labor_rate = float(self.labor_rate.get())
            mileage = float(self.initial_mileage.get())
            recovery_miles = float(self.recovery_miles.get())
            tow_base = float(self.tow_base_fee.get())
            miles_included = float(self.mileage_included.get())
            mileage_rate = float(self.mileage_rate.get())
            certified_first = float(self.certified_mail_first.get())
            certified_second = float(self.certified_mail_second.get())
        except ValueError:
            messagebox.showerror("Intake", "Please check numeric fields.")
            return

        customer = Customer(
            name=self.cust_name.get(),
            phone=self.cust_phone.get(),
            address=self.cust_address.get(),
        )
        vehicle = Vehicle(
            plate=self.plate.get(),
            vin=self.vin.get(),
            vehicle_type=self.vehicle_type.get(),
            make=self.make.get(),
            model=self.model.get(),
            color=self.color.get(),
            initial_mileage=mileage,
        )

        contract = build_contract(
            self.storage_data,
            customer,
            vehicle,
            self.start_date.get(),
            self.contract_type.get(),
            daily_rate,
            tow_fee,
            impound_fee,
            admin_fee,
            tow_base,
            miles_included,
            mileage_rate,
            certified_first,
            certified_second,
            labor_minutes,
            labor_rate,
            recovery_miles,
            labor_minutes,
            labor_rate,
        )
        save_data(self.storage_data)
        messagebox.showinfo("Intake", f"Created contract #{contract.contract_id}")
        self.refresh_contracts()
        self._reset_intake_form()
        self.notebook.select(self.contract_tab)

    def _reset_intake_form(self) -> None:
        self.contract_type.set("Storage Only")
        self.cust_name.set("")
        self.cust_phone.set("")
        self.cust_address.set("")
        self.plate.set("")
        self.vin.set("")
        self.vehicle_type.set("Car")
        self.make.set("")
        self.model.set("")
        self.color.set("")
        self.initial_mileage.set("0")
        self.recovery_miles.set("0")
        self.extra_labor.set("0")
        self.labor_rate.set("45")
        self.start_date.set(datetime.today().strftime(DATE_FORMAT))
        self._load_defaults_for_type()

        self.notebook.select(self.contract_tab)

    def _add_labeled_entry(self, parent: tk.Widget, label: str, var: tk.StringVar, width: int = 25) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text=label, width=20).pack(side=tk.LEFT)
        ttk.Entry(row, textvariable=var, width=width).pack(side=tk.LEFT)

    # ------------------------------------------------------------------
    # Fee template tab
    # ------------------------------------------------------------------
    def _build_fee_tab(self) -> None:
        frame = ttk.Frame(self.fee_tab, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        self.fee_tree = ttk.Treeview(
            frame,
            columns=("type", "daily", "tow", "impound", "admin", "tow_base", "mileage_rate", "labor_rate"),
            columns=("type", "daily", "tow", "impound", "admin"),
            show="headings",
            height=8,
        )
        for col, text, width in [
            ("type", "Vehicle Type", 160),
            ("daily", "Daily Storage", 120),
            ("tow", "Tow Fee", 100),
            ("impound", "Impound", 100),
            ("admin", "Admin", 100),
            ("tow_base", "Tow Base", 100),
            ("mileage_rate", "Mileage Rate", 110),
            ("labor_rate", "Labor/hr", 90),
        ]:
            self.fee_tree.heading(col, text=text)
            self.fee_tree.column(col, width=width)
        self.fee_tree.bind("<<TreeviewSelect>>", lambda *_: self._populate_fee_form())
        self.fee_tree.pack(fill=tk.X, pady=(0, 8))

        form = ttk.Frame(frame)
        form.pack(fill=tk.X, pady=4)
        self.fee_type = tk.StringVar()
        self.fee_daily = tk.StringVar()
        self.fee_tow = tk.StringVar()
        self.fee_impound = tk.StringVar()
        self.fee_admin = tk.StringVar()
        self.fee_tow_base = tk.StringVar()
        self.fee_mileage_included = tk.StringVar()
        self.fee_mileage_rate = tk.StringVar()
        self.fee_labor_rate = tk.StringVar()
        self.fee_cert_first = tk.StringVar()
        self.fee_cert_second = tk.StringVar()

        self._add_labeled_entry(form, "Vehicle Type", self.fee_type)
        self._add_labeled_entry(form, "Daily Storage", self.fee_daily)
        self._add_labeled_entry(form, "Tow Fee", self.fee_tow)
        self._add_labeled_entry(form, "Impound Fee", self.fee_impound)
        self._add_labeled_entry(form, "Admin Fee", self.fee_admin)
        self._add_labeled_entry(form, "Tow Base", self.fee_tow_base)
        self._add_labeled_entry(form, "Mileage Included", self.fee_mileage_included)
        self._add_labeled_entry(form, "Mileage Rate", self.fee_mileage_rate)
        self._add_labeled_entry(form, "Labor Rate", self.fee_labor_rate)
        self._add_labeled_entry(form, "Cert Mail (1st)", self.fee_cert_first)
        self._add_labeled_entry(form, "Cert Mail (2nd)", self.fee_cert_second)

        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X, pady=4)
        ttk.Button(btns, text="Save", command=self._save_fee_template).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Reset to Defaults", command=self._reset_templates).pack(side=tk.LEFT, padx=4)

        self._refresh_fee_tree()

    def _refresh_fee_tree(self) -> None:
        for row in self.fee_tree.get_children():
            self.fee_tree.delete(row)
        for vehicle_type, fees in self.fee_templates.items():
            self.fee_tree.insert(
                "",
                tk.END,
                iid=vehicle_type,
                values=(
                    vehicle_type,
                    f"${fees['daily_rate']:.2f}",
                    f"${fees['tow_fee']:.2f}",
                    f"${fees['impound_fee']:.2f}",
                    f"${fees['admin_fee']:.2f}",
                    f"${fees.get('tow_base_fee', 0.0):.2f}",
                    f"${fees.get('mileage_rate', 0.0):.2f}",
                    f"${fees.get('labor_rate', 0.0):.2f}",
                ),
            )

    def _populate_fee_form(self) -> None:
        sel = self.fee_tree.selection()
        if not sel:
            return
        vehicle_type = sel[0]
        fees = self.fee_templates.get(vehicle_type, default_fee_schedule("Car"))
        self.fee_type.set(vehicle_type)
        self.fee_daily.set(str(fees["daily_rate"]))
        self.fee_tow.set(str(fees["tow_fee"]))
        self.fee_impound.set(str(fees["impound_fee"]))
        self.fee_admin.set(str(fees["admin_fee"]))
        self.fee_tow_base.set(str(fees.get("tow_base_fee", 0.0)))
        self.fee_mileage_included.set(str(fees.get("mileage_included", 0.0)))
        self.fee_mileage_rate.set(str(fees.get("mileage_rate", 0.0)))
        self.fee_labor_rate.set(str(fees.get("labor_rate", 0.0)))
        self.fee_cert_first.set(str(fees.get("certified_mail_fee_first", 0.0)))
        self.fee_cert_second.set(str(fees.get("certified_mail_fee_second", 0.0)))

    def _save_fee_template(self) -> None:
        try:
            daily = float(self.fee_daily.get())
            tow = float(self.fee_tow.get())
            impound = float(self.fee_impound.get())
            admin = float(self.fee_admin.get())
            tow_base = float(self.fee_tow_base.get())
            miles_included = float(self.fee_mileage_included.get())
            mileage_rate = float(self.fee_mileage_rate.get())
            labor_rate = float(self.fee_labor_rate.get())
            cert_first = float(self.fee_cert_first.get())
            cert_second = float(self.fee_cert_second.get())
        except ValueError:
            messagebox.showerror("Fees", "Please enter numeric values")
            return
        vehicle_type = self.fee_type.get().strip() or "Custom"
        self.fee_templates[vehicle_type] = {
            "daily_rate": daily,
            "tow_fee": tow,
            "impound_fee": impound,
            "admin_fee": admin,
            "tow_base_fee": tow_base,
            "mileage_included": miles_included,
            "mileage_rate": mileage_rate,
            "labor_rate": labor_rate,
            "certified_mail_fee_first": cert_first,
            "certified_mail_fee_second": cert_second,
        }
        save_fee_templates(self.fee_templates)
        self._refresh_fee_tree()
        messagebox.showinfo("Fees", f"Saved template for {vehicle_type}")

    def _reset_templates(self) -> None:
        from lot_logic import DEFAULT_VEHICLE_FEES

        self.fee_templates = DEFAULT_VEHICLE_FEES.copy()
        save_fee_templates(self.fee_templates)
        self._refresh_fee_tree()


if __name__ == "__main__":
    app = LotApp()
    app.mainloop()
