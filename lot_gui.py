"""PyQt6 UI for the Storage & Recovery Lot program."""
from __future__ import annotations

import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QLineEdit, QComboBox, QTextEdit, QMessageBox, QDialog,
    QFormLayout, QSpinBox, QCheckBox, QFileDialog, QMenu, QMenuBar,
    QHeaderView, QFrame, QScrollArea, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, QSize, QPoint, pyqtSignal, QEvent
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QAction

from lot_logic import (
    add_notice, balance, default_fee_schedule,
    format_contract_summary, format_contract_record, lien_eligibility,
    lien_timeline, load_data, load_fee_templates, past_due_status,
    record_payment, save_data, save_fee_templates, storage_days,
)
from lot_models import Customer, Vehicle, StorageContract, StorageData, DATE_FORMAT


# Color Themes
THEMES = {
    "Light": {
        "bg": "#f5f5f5",
        "fg": "#000000",
        "select_bg": "#0078d4",
        "select_fg": "#ffffff",
        "tree_odd": "#ffffff",
        "tree_even": "#f0f0f0",
        "button_bg": "#0078d4",
        "button_fg": "#ffffff",
        "button_hover": "#106ebe",
        "entry_bg": "#ffffff",
        "entry_fg": "#000000",
        "frame_bg": "#f5f5f5",
        "accent": "#0078d4",
        "border": "#e1e4e8",
        "menu_bg": "#f5f6f7",
        "titlebar_bg": "#2d2d30",
        "titlebar_fg": "#ffffff",
    },
    "Dark": {
        "bg": "#1e1e1e",
        "fg": "#e0e0e0",
        "select_bg": "#0e639c",
        "select_fg": "#ffffff",
        "tree_odd": "#252526",
        "tree_even": "#2d2d30",
        "button_bg": "#0e639c",
        "button_fg": "#ffffff",
        "button_hover": "#1177bb",
        "entry_bg": "#2d2d30",
        "entry_fg": "#e0e0e0",
        "frame_bg": "#1e1e1e",
        "accent": "#0e639c",
        "border": "#3e3e42",
        "menu_bg": "#2d2d30",
        "titlebar_bg": "#2d2d30",
        "titlebar_fg": "#ffffff",
    },
}


class CustomTitleBar(QWidget):
    """Custom title bar with menu bar and window controls."""
    """Custom title bar with window controls."""
    
    close_clicked = pyqtSignal()
    minimize_clicked = pyqtSignal()
    maximize_clicked = pyqtSignal()
    
    def __init__(self, parent=None, theme_colors=None):
        super().__init__(parent)
        self.theme_colors = theme_colors or THEMES["Dark"]
        self.drag_position = QPoint()
        self.menu_callbacks = {}  # Store menu callbacks
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the title bar UI."""
        self.setFixedHeight(40)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.theme_colors['titlebar_bg']};
                color: {self.theme_colors['titlebar_fg']};
            }}
        """)
        
        # Clear existing layout if any
        if self.layout():
            QWidget().setLayout(self.layout())
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 0, 0)
        layout.setSpacing(0)
        
        # Menu button style
        menu_btn_style = f"""
            QPushButton {{
                border: none;
                padding: 10px 15px;
                color: {self.theme_colors['titlebar_fg']};
                background-color: transparent;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {self.theme_colors['button_hover']};
            }}
        """
        
        # File menu button (left)
        self.file_btn = QPushButton("File")
        self.file_btn.setFlat(True)
        self.file_btn.setStyleSheet(menu_btn_style)
        self.file_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.file_btn)
        
        # Edit menu button
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setFlat(True)
        self.edit_btn.setStyleSheet(menu_btn_style)
        self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.edit_btn)
        
        # Help menu button
        self.help_btn = QPushButton("Help")
        self.help_btn.setFlat(True)
        self.help_btn.setStyleSheet(menu_btn_style)
        self.help_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.help_btn)
        
        # Reconnect menu callbacks if they exist
        if 'file' in self.menu_callbacks:
            self.file_btn.clicked.connect(self.menu_callbacks['file'])
        if 'edit' in self.menu_callbacks:
            self.edit_btn.clicked.connect(self.menu_callbacks['edit'])
        if 'help' in self.menu_callbacks:
            self.help_btn.clicked.connect(self.menu_callbacks['help'])
        
        layout.addStretch()
        
        # App title (centered) - this will be the drag handle
        self.title_label = QLabel("Storage & Recovery Lot")
        self.title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.title_label.setStyleSheet(f"color: {self.theme_colors['titlebar_fg']}; padding: 10px;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Install event filter on title label for dragging
        self.title_label.installEventFilter(self)
        
        layout.addStretch()
        
        # Search bar (before window controls)
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet(f"color: {self.theme_colors['titlebar_fg']}; padding: 0 5px;")
        layout.addWidget(search_icon)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search...")
        self.search_box.setFixedWidth(200)
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.theme_colors['entry_bg']};
                color: {self.theme_colors['entry_fg']};
                border: 1px solid {self.theme_colors['border']};
                padding: 6px 10px;
                border-radius: 4px;
            }}
            QLineEdit:focus {{
                border: 1px solid {self.theme_colors['accent']};
            }}
        """)
        layout.addWidget(self.search_box)
        
        # Spacing before window controls
        layout.addSpacing(10)
        
        # Window control buttons (right)
        btn_style = """
            QPushButton {
                border: none;
                padding: 10px 15px;
                color: %s;
                background-color: transparent;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: %s;
            }
        """
        
        self.min_btn = QPushButton("—")
        self.min_btn.setStyleSheet(btn_style % (self.theme_colors['titlebar_fg'], self.theme_colors['button_hover']))
        self.min_btn.clicked.connect(self.minimize_clicked.emit)
        self.min_btn.setFixedSize(45, 40)
        layout.addWidget(self.min_btn)
        
        self.max_btn = QPushButton("□")
        self.max_btn.setStyleSheet(btn_style % (self.theme_colors['titlebar_fg'], self.theme_colors['button_hover']))
        self.max_btn.clicked.connect(self.maximize_clicked.emit)
        self.max_btn.setFixedSize(45, 40)
        layout.addWidget(self.max_btn)
        
        close_style = btn_style % (self.theme_colors['titlebar_fg'], "#e81123") + \
                     "QPushButton:hover { color: #ffffff; }"
        self.close_btn = QPushButton("✕")
        self.close_btn.setStyleSheet(close_style)
        self.close_btn.clicked.connect(self.close_clicked.emit)
        self.close_btn.setFixedSize(45, 40)
        layout.addWidget(self.close_btn)
    
    def eventFilter(self, obj, event):
        """Handle dragging from title label only."""
        if obj == self.title_label:
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.drag_position = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
                    return True
            elif event.type() == QEvent.Type.MouseMove:
                if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_position'):
                    self.window().move(event.globalPosition().toPoint() - self.drag_position)
                    return True
            elif event.type() == QEvent.Type.MouseButtonRelease:
                if hasattr(self, 'drag_position'):
                    delattr(self, 'drag_position')
                    return True
        return super().eventFilter(obj, event)


class ContractEditDialog(QDialog):
    """Dialog for editing an existing contract."""
    
    def __init__(self, contract: StorageContract, fee_templates: Dict, parent=None):
        super().__init__(parent)
        self.contract = contract
        self.fee_templates = fee_templates
        self.setWindowTitle(f"Edit Contract #{contract.contract_id}")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the edit dialog UI."""
        layout = QVBoxLayout(self)
        
        # Scroll area for form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(400)
        
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        # Customer info
        form_layout.addRow(QLabel("<b>Customer Information</b>"))
        self.customer_name = QLineEdit(self.contract.customer.name)
        form_layout.addRow("Name:", self.customer_name)
        
        self.customer_phone = QLineEdit(self.contract.customer.phone)
        form_layout.addRow("Phone:", self.customer_phone)
        
        self.customer_address = QLineEdit(self.contract.customer.address)
        form_layout.addRow("Address:", self.customer_address)
        
        form_layout.addRow(QLabel(""))  # Spacer
        
        # Vehicle info
        form_layout.addRow(QLabel("<b>Vehicle Information</b>"))
        self.vehicle_plate = QLineEdit(self.contract.vehicle.plate)
        form_layout.addRow("Plate:", self.vehicle_plate)
        
        self.vehicle_vin = QLineEdit(self.contract.vehicle.vin)
        form_layout.addRow("VIN:", self.vehicle_vin)
        
        self.vehicle_make = QLineEdit(self.contract.vehicle.make)
        form_layout.addRow("Make:", self.vehicle_make)
        
        self.vehicle_model = QLineEdit(self.contract.vehicle.model)
        form_layout.addRow("Model:", self.vehicle_model)
        
        self.vehicle_year = QLineEdit(str(self.contract.vehicle.year) if self.contract.vehicle.year else "")
        form_layout.addRow("Year:", self.vehicle_year)
        
        self.vehicle_color = QLineEdit(self.contract.vehicle.color)
        form_layout.addRow("Color:", self.vehicle_color)
        
        form_layout.addRow(QLabel(""))  # Spacer
        
        # Contract details
        form_layout.addRow(QLabel("<b>Contract Details</b>"))
        
        self.admin_fee = QLineEdit(str(self.contract.admin_fee))
        form_layout.addRow("Admin Fee:", self.admin_fee)
        
        # Tow fields (only show if tow contract)
        if self.contract.contract_type.lower() == "tow":
            form_layout.addRow(QLabel("<b>Tow Details</b>"))
            self.tow_base_fee = QLineEdit(str(self.contract.tow_base_fee))
            form_layout.addRow("Base Fee:", self.tow_base_fee)
            
            self.tow_miles_used = QLineEdit(str(self.contract.tow_miles_used))
            form_layout.addRow("Miles:", self.tow_miles_used)
            
            self.tow_labor_hours = QLineEdit(str(self.contract.tow_labor_hours))
            form_layout.addRow("Labor Hours:", self.tow_labor_hours)
            
        # Recovery fields (only show if recovery contract)
        if self.contract.contract_type.lower() == "recovery":
            form_layout.addRow(QLabel("<b>Recovery Details</b>"))
            self.notices_sent = QLineEdit(str(self.contract.notices_sent))
            form_layout.addRow("Notices Sent:", self.notices_sent)
        
        # Status
        form_layout.addRow(QLabel(""))  # Spacer
        self.status = QComboBox()
        self.status.addItems(["Active", "Closed", "Released"])
        self.status.setCurrentText(self.contract.status)
        form_layout.addRow("Status:", self.status)
        
        scroll.setWidget(form_widget)
        layout.addWidget(scroll)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
    
    def get_contract(self) -> StorageContract:
        """Get the updated contract with edited values."""
        # Update customer
        self.contract.customer.name = self.customer_name.text().strip()
        self.contract.customer.phone = self.customer_phone.text().strip()
        self.contract.customer.address = self.customer_address.text().strip()
        
        # Update vehicle
        self.contract.vehicle.plate = self.vehicle_plate.text().strip()
        self.contract.vehicle.vin = self.vehicle_vin.text().strip()
        self.contract.vehicle.make = self.vehicle_make.text().strip()
        self.contract.vehicle.model = self.vehicle_model.text().strip()
        self.contract.vehicle.color = self.vehicle_color.text().strip()
        
        try:
            year_text = self.vehicle_year.text().strip()
            self.contract.vehicle.year = int(year_text) if year_text else None
        except ValueError:
            pass
        
        # Update admin fee
        try:
            self.contract.admin_fee = float(self.admin_fee.text() or 0)
        except ValueError:
            pass
        
        # Update tow fields if applicable
        if self.contract.contract_type.lower() == "tow":
            try:
                self.contract.tow_base_fee = float(self.tow_base_fee.text() or 0)
                self.contract.tow_miles_used = float(self.tow_miles_used.text() or 0)
                self.contract.tow_labor_hours = float(self.tow_labor_hours.text() or 0)
            except ValueError:
                pass
        
        # Update recovery fields if applicable
        if self.contract.contract_type.lower() == "recovery":
            try:
                self.contract.notices_sent = int(self.notices_sent.text() or 0)
            except ValueError:
                pass
        
        # Update status
        self.contract.status = self.status.currentText()
        
        return self.contract


class LotAppQt(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.current_theme = "Dark"
        self.storage_data: StorageData = load_data()
        self.fee_templates: Dict[str, Dict[str, float]] = load_fee_templates()
        
        self.init_ui()
        self.load_theme_preference()
        self.apply_theme(self.current_theme)
        
    def init_ui(self):
        """Initialize the user interface."""
        # Frameless window for custom title bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setGeometry(100, 100, 1200, 700)
        self.setMinimumSize(800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Custom title bar
        self.title_bar = CustomTitleBar(self, THEMES[self.current_theme])
        self.title_bar.close_clicked.connect(self.close)
        self.title_bar.minimize_clicked.connect(self.showMinimized)
        self.title_bar.maximize_clicked.connect(self.toggle_maximize)
        main_layout.addWidget(self.title_bar)
        
        # Create menus as instance variables
        self.file_menu = QMenu(self)
        print_action = QAction("Print", self)
        print_action.triggered.connect(self.print_record)
        self.file_menu.addAction(print_action)
        
        export_action = QAction("Export Summary", self)
        export_action.triggered.connect(self.export_summary)
        self.file_menu.addAction(export_action)
        
        self.file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        self.file_menu.addAction(exit_action)
        
        self.edit_menu = QMenu(self)
        theme_action = QAction("Toggle Theme (Dark/Light)", self)
        theme_action.triggered.connect(self.toggle_theme)
        self.edit_menu.addAction(theme_action)
        
        self.help_menu = QMenu(self)
        help_action = QAction("Help", self)
        help_action.triggered.connect(self.show_help)
        self.help_menu.addAction(help_action)
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        self.help_menu.addAction(about_action)
        
        docs_action = QAction("Documentation", self)
        docs_action.triggered.connect(self.show_documentation)
        self.help_menu.addAction(docs_action)
        
        # Store menu callbacks and connect buttons
        self.title_bar.menu_callbacks = {
            'file': self.show_file_menu,
            'edit': self.show_edit_menu,
            'help': self.show_help_menu
        }
        self.title_bar.file_btn.clicked.connect(self.show_file_menu)
        self.title_bar.edit_btn.clicked.connect(self.show_edit_menu)
        self.title_bar.help_btn.clicked.connect(self.show_help_menu)
        
        # Connect search box
        self.title_bar.search_box.textChanged.connect(self.filter_contracts)
        
        # Content area with padding
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)
        main_layout.addWidget(content_widget)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        content_layout.addWidget(self.tabs)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("padding: 5px;")
        content_layout.addWidget(self.status_label)
        
        # Create tabs
        self.create_contracts_tab()
        self.create_intake_tab()
        self.create_fee_tab()
        

    
    def create_contracts_tab(self):
        """Create the contracts list tab."""
        contracts_widget = QWidget()
        layout = QVBoxLayout(contracts_widget)
        
        # Contract table
        self.contract_table = QTableWidget()
        self.contract_table.setColumnCount(7)
        self.contract_table.setHorizontalHeaderLabels([
            "ID", "Customer", "Vehicle", "Type", "Start Date", "Balance", "Status"
        ])
        self.contract_table.horizontalHeader().setStretchLastSection(True)
        self.contract_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.contract_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.contract_table.itemSelectionChanged.connect(self.on_contract_selected)
        self.contract_table.cellDoubleClicked.connect(self.edit_contract)
        layout.addWidget(self.contract_table)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        edit_btn = QPushButton("Edit Contract")
        edit_btn.clicked.connect(self.edit_contract)
        btn_layout.addWidget(edit_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Contract details
        details_label = QLabel("Contract Details")
        details_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(details_label)
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(200)
        layout.addWidget(self.summary_text)
        
        self.tabs.addTab(contracts_widget, "Contracts")
        self.refresh_contracts()
        
    def create_intake_tab(self):
        """Create the intake form tab."""
        intake_widget = QScrollArea()
        intake_widget.setWidgetResizable(True)
        
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setSpacing(10)
        
        # CONTRACT TYPE AT TOP
        self.contract_type = QComboBox()
        self.contract_type.addItems(["Storage", "Tow", "Recovery"])
        self.contract_type.currentTextChanged.connect(self.on_contract_type_changed)
        form_layout.addRow("Contract Type:", self.contract_type)
        
        form_layout.addRow(QLabel(""))  # Spacer
        
        # Customer fields
        self.customer_name = QLineEdit()
        self.customer_phone = QLineEdit()
        self.customer_address = QLineEdit()
        form_layout.addRow("Customer Name:", self.customer_name)
        form_layout.addRow("Phone:", self.customer_phone)
        form_layout.addRow("Address:", self.customer_address)
        
        form_layout.addRow(QLabel(""))  # Spacer
        
        # Vehicle fields
        self.vehicle_type = QComboBox()
        self.vehicle_type.addItems(list(self.fee_templates.keys()))
        self.vehicle_type.currentTextChanged.connect(self.load_defaults_for_type)
        form_layout.addRow("Vehicle Type:", self.vehicle_type)
        
        self.vehicle_make = QLineEdit()
        self.vehicle_model = QLineEdit()
        self.vehicle_year = QLineEdit()
        self.vehicle_color = QLineEdit()
        self.vehicle_plate = QLineEdit()
        self.vehicle_vin = QLineEdit()
        
        form_layout.addRow("Make:", self.vehicle_make)
        form_layout.addRow("Model:", self.vehicle_model)
        form_layout.addRow("Year:", self.vehicle_year)
        form_layout.addRow("Color:", self.vehicle_color)
        form_layout.addRow("License Plate:", self.vehicle_plate)
        form_layout.addRow("VIN:", self.vehicle_vin)
        
        form_layout.addRow(QLabel(""))  # Spacer
        
        # Storage rate mode (all contract types)
        self.rate_mode = QComboBox()
        self.rate_mode.addItems(["Daily", "Weekly", "Monthly"])
        form_layout.addRow("Storage Rate Mode:", self.rate_mode)
        
        form_layout.addRow(QLabel(""))  # Spacer
        
        # Common fields
        self.admin_fee = QLineEdit()
        form_layout.addRow("Admin Fee (max $250):", self.admin_fee)
        
        # Tow-specific fields
        self.tow_section_label = QLabel("=== Tow Fees (Voluntary) ===")
        form_layout.addRow(self.tow_section_label)
        
        self.tow_base_fee = QLineEdit()
        self.tow_mileage_rate = QLineEdit()
        self.tow_miles_used = QLineEdit()
        self.tow_hourly_labor_rate = QLineEdit()
        self.tow_labor_hours = QLineEdit()
        self.tow_after_hours_fee = QLineEdit()
        
        form_layout.addRow("Tow Base Fee:", self.tow_base_fee)
        form_layout.addRow("Tow Mileage Rate:", self.tow_mileage_rate)
        form_layout.addRow("Tow Miles Used:", self.tow_miles_used)
        form_layout.addRow("Tow Hourly Labor Rate:", self.tow_hourly_labor_rate)
        form_layout.addRow("Tow Labor Hours:", self.tow_labor_hours)
        form_layout.addRow("After Hours Fee:", self.tow_after_hours_fee)
        
        # Store tow field widgets for show/hide
        self.tow_fields = [
            self.tow_section_label,
            form_layout.labelForField(self.tow_base_fee),
            self.tow_base_fee,
            form_layout.labelForField(self.tow_mileage_rate),
            self.tow_mileage_rate,
            form_layout.labelForField(self.tow_miles_used),
            self.tow_miles_used,
            form_layout.labelForField(self.tow_hourly_labor_rate),
            self.tow_hourly_labor_rate,
            form_layout.labelForField(self.tow_labor_hours),
            self.tow_labor_hours,
            form_layout.labelForField(self.tow_after_hours_fee),
            self.tow_after_hours_fee,
        ]
        
        form_layout.addRow(QLabel(""))  # Spacer
        
        # Recovery-specific fields
        self.recovery_section_label = QLabel("=== Recovery Fees (Involuntary) ===")
        form_layout.addRow(self.recovery_section_label)
        
        self.recovery_handling_fee = QLineEdit()
        self.lien_processing_fee = QLineEdit()
        self.cert_mail_fee = QLineEdit()
        self.notices_sent = QLineEdit()
        self.title_search_fee = QLineEdit()
        self.dmv_fee = QLineEdit()
        self.sale_fee = QLineEdit()
        
        form_layout.addRow("Recovery Handling Fee:", self.recovery_handling_fee)
        form_layout.addRow("Lien Processing Fee (max $250):", self.lien_processing_fee)
        form_layout.addRow("Certified Mail Fee (per notice):", self.cert_mail_fee)
        form_layout.addRow("Notices Sent (count):", self.notices_sent)
        form_layout.addRow("Title Search Fee:", self.title_search_fee)
        form_layout.addRow("DMV Fee:", self.dmv_fee)
        form_layout.addRow("Sale Fee:", self.sale_fee)
        
        # Store recovery field widgets for show/hide
        self.recovery_fields = [
            self.recovery_section_label,
            form_layout.labelForField(self.recovery_handling_fee),
            self.recovery_handling_fee,
            form_layout.labelForField(self.lien_processing_fee),
            self.lien_processing_fee,
            form_layout.labelForField(self.cert_mail_fee),
            self.cert_mail_fee,
            form_layout.labelForField(self.notices_sent),
            self.notices_sent,
            form_layout.labelForField(self.title_search_fee),
            self.title_search_fee,
            form_layout.labelForField(self.dmv_fee),
            self.dmv_fee,
            form_layout.labelForField(self.sale_fee),
            self.sale_fee,
        ]
        
        # Buttons
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Create Contract")
        create_btn.clicked.connect(self.create_contract)
        clear_btn = QPushButton("Clear Form")
        clear_btn.clicked.connect(self.clear_intake_form)
        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        form_layout.addRow(btn_layout)
        
        intake_widget.setWidget(form_widget)
        self.tabs.addTab(intake_widget, "Intake")
        
        # Load defaults
        self.load_defaults_for_type()
        self.on_contract_type_changed()
        
    def create_fee_tab(self):
        """Create the fee templates tab."""
        fee_widget = QScrollArea()
        fee_widget.setWidgetResizable(True)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        
        info_label = QLabel("Edit fee templates for each vehicle type. Changes are saved when you click 'Save Fee Templates'.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        self.fee_table = QTableWidget()
        self.fee_table.setColumnCount(16)
        self.fee_table.setHorizontalHeaderLabels([
            "Vehicle Type",
            "Daily Storage",
            "Weekly Storage", 
            "Monthly Storage",
            "Tow Base",
            "Tow Mileage Rate",
            "Tow Labor Rate",
            "After Hours",
            "Recovery Handling",
            "Lien Processing",
            "Cert Mail",
            "Title Search",
            "DMV Fee",
            "Sale Fee",
            "Admin Fee",
            "Labor Rate"
        ])
        self.fee_table.horizontalHeader().setStretchLastSection(False)
        for i in range(16):
            self.fee_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        layout.addWidget(self.fee_table)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Fee Templates")
        save_btn.clicked.connect(self.save_fee_templates_action)
        btn_layout.addWidget(save_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        fee_widget.setWidget(content)
        self.tabs.addTab(fee_widget, "Fee Templates")
        self.refresh_fee_table()
        
    def toggle_maximize(self):
        """Toggle between maximized and normal state."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    
    def toggle_theme(self):
        """Toggle between Dark and Light themes."""
        new_theme = "Light" if self.current_theme == "Dark" else "Dark"
        self.apply_theme(new_theme)
        self.save_theme_preference()
    
    def show_file_menu(self):
        """Show File menu."""
        pos = self.title_bar.file_btn.mapToGlobal(self.title_bar.file_btn.rect().bottomLeft())
        self.file_menu.exec(pos)
    
    def show_edit_menu(self):
        """Show Edit menu."""
        pos = self.title_bar.edit_btn.mapToGlobal(self.title_bar.edit_btn.rect().bottomLeft())
        self.edit_menu.exec(pos)
    
    def show_help_menu(self):
        """Show Help menu."""
        pos = self.title_bar.help_btn.mapToGlobal(self.title_bar.help_btn.rect().bottomLeft())
        self.help_menu.exec(pos)
    
    def populate_contract_row(self, row_index: int, contract: StorageContract):
        """Populate a single contract row with status logic and styling."""
        # Calculate balance
        bal = balance(contract)
        vehicle = f"{contract.vehicle.vehicle_type} {contract.vehicle.plate}"
        
        # Get status information from lot_logic
        past_due, days_past_due = past_due_status(contract)
        is_lien_eligible, lien_status_text = lien_eligibility(contract)
        timeline = lien_timeline(contract)
        is_sale_eligible = timeline.get("is_sale_eligible", False)
        
        # Determine display status based on conditions
        if is_sale_eligible:
            display_status = "SALE ELIGIBLE"
        elif is_lien_eligible:
            display_status = lien_status_text
        elif past_due:
            display_status = f"Past Due ({days_past_due} days)"
        else:
            display_status = contract.status
        
        # Create table items
        id_item = QTableWidgetItem(str(contract.contract_id))
        name_item = QTableWidgetItem(contract.customer.name)
        vehicle_item = QTableWidgetItem(vehicle)
        type_item = QTableWidgetItem(contract.contract_type)
        date_item = QTableWidgetItem(contract.start_date)
        balance_item = QTableWidgetItem(f"${bal:.2f}")
        status_item = QTableWidgetItem(display_status)
        
        # Apply red color to status if any critical condition is met
        if past_due or is_lien_eligible or is_sale_eligible:
            status_item.setForeground(QColor("red"))
        
        # Set items in table
        self.contract_table.setItem(row_index, 0, id_item)
        self.contract_table.setItem(row_index, 1, name_item)
        self.contract_table.setItem(row_index, 2, vehicle_item)
        self.contract_table.setItem(row_index, 3, type_item)
        self.contract_table.setItem(row_index, 4, date_item)
        self.contract_table.setItem(row_index, 5, balance_item)
        self.contract_table.setItem(row_index, 6, status_item)
            
    def refresh_contracts(self):
        """Refresh the contract table."""
        self.contract_table.setRowCount(len(self.storage_data.contracts))
        
        for i, contract in enumerate(self.storage_data.contracts):
            self.populate_contract_row(i, contract)
            
    def on_contract_selected(self):
        """Handle contract selection."""
        selected_rows = self.contract_table.selectedIndexes()
        if not selected_rows:
            self.summary_text.clear()
            return
            
        row = selected_rows[0].row()
        contract = self.storage_data.contracts[row]
        
        # Get basic contract summary
        summary = format_contract_summary(contract)
        
        # Get lien and sale timeline information
        timeline = lien_timeline(contract)
        is_lien_eligible, lien_status = lien_eligibility(contract)
        
        # Build lien & sale timeline section
        timeline_section = "\n\n" + "="*60 + "\n"
        timeline_section += "LIEN & SALE TIMELINE\n"
        timeline_section += "="*60 + "\n\n"
        
        # First notice information
        timeline_section += f"First Notice Due:  {timeline['first_notice_due']}\n"
        if contract.first_notice_sent_date:
            timeline_section += f"First Notice Sent: {contract.first_notice_sent_date}\n"
        else:
            timeline_section += "First Notice Sent: NOT SENT\n"
        
        timeline_section += "\n"
        
        # Second notice information
        timeline_section += f"Second Notice Due:  {timeline['second_notice_due']}\n"
        if contract.second_notice_sent_date:
            timeline_section += f"Second Notice Sent: {contract.second_notice_sent_date}\n"
        else:
            timeline_section += "Second Notice Sent: NOT SENT\n"
        
        timeline_section += "\n"
        
        # Lien eligibility
        timeline_section += f"Lien Eligible Date: {timeline['lien_eligible_date']}\n"
        if is_lien_eligible:
            timeline_section += "Lien Status:        ✓ LIEN ELIGIBLE\n"
        else:
            timeline_section += f"Lien Status:        Not yet eligible ({lien_status})\n"
        
        timeline_section += "\n"
        
        # Sale eligibility (based on vehicle age and contract type)
        if contract.contract_type == "Tow & Recovery" and contract.vehicle.year:
            vehicle_age = datetime.today().year - contract.vehicle.year
            sale_wait = 35 if vehicle_age >= 3 else 50
            timeline_section += f"Vehicle Age:        {vehicle_age} years ({contract.vehicle.year})\n"
            timeline_section += f"Sale Wait Period:   {sale_wait} days after lien ({sale_wait} days for {'3+ year' if sale_wait == 35 else 'newer'} vehicles)\n"
        
        timeline_section += f"Earliest Sale Date: {timeline['sale_earliest_date']}\n"
        
        if timeline['is_sale_eligible']:
            timeline_section += "Sale Status:        ✓ SALE ELIGIBLE\n"
        elif contract.contract_type == "Tow & Recovery":
            timeline_section += "Sale Status:        Not yet eligible (see warnings below)\n"
        else:
            timeline_section += "Sale Status:        N/A (Storage Only contracts do not have sale process)\n"
        
        # Warnings and alerts
        if timeline['warnings']:
            timeline_section += "\n" + "-"*60 + "\n"
            timeline_section += "ALERTS & WARNINGS:\n"
            timeline_section += "-"*60 + "\n"
            for warning in timeline['warnings']:
                timeline_section += f"{warning}\n"
        
        # Combine and display
        full_summary = summary + timeline_section
        self.summary_text.setText(full_summary)
        
    def filter_contracts(self, text):
        """Filter contracts based on search text."""
        if not text:
            self.refresh_contracts()
            return
            
        text = text.lower()
        filtered = [c for c in self.storage_data.contracts 
                   if text in c.customer.name.lower() or 
                      text in c.vehicle.plate.lower() or
                      text in str(c.contract_id)]
        
        self.contract_table.setRowCount(len(filtered))
        for i, contract in enumerate(filtered):
            self.populate_contract_row(i, contract)
    
    def edit_contract(self):
        """Open dialog to edit selected contract."""
        selected_rows = self.contract_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a contract to edit.")
            return
        
        row = selected_rows[0].row()
        contract = self.storage_data.contracts[row]
        
        # Create edit dialog
        dialog = ContractEditDialog(contract, self.fee_templates, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get updated contract
            updated_contract = dialog.get_contract()
            # Replace in list
            self.storage_data.contracts[row] = updated_contract
            # Save
            save_data(self.storage_data)
            # Refresh display
            self.refresh_contracts()
            QMessageBox.information(self, "Success", f"Contract #{contract.contract_id} updated successfully!")
            
    def on_contract_type_changed(self):
        """Show/hide fields based on contract type selection."""
        contract_type = self.contract_type.currentText().lower()
        
        # Show/hide tow fields
        show_tow = (contract_type == "tow")
        for widget in self.tow_fields:
            if widget:
                widget.setVisible(show_tow)
        
        # Show/hide recovery fields
        show_recovery = (contract_type == "recovery")
        for widget in self.recovery_fields:
            if widget:
                widget.setVisible(show_recovery)
    
    def load_defaults_for_type(self):
        """Load default fees for selected vehicle type."""
        vtype = self.vehicle_type.currentText()
        if vtype not in self.fee_templates:
            return
            
        fees = self.fee_templates[vtype]
        
        # Common
        self.admin_fee.setText(str(fees.get("admin_fee", "0")))
        
        # Tow fees
        self.tow_base_fee.setText(str(fees.get("tow_base_fee", "0")))
        self.tow_mileage_rate.setText(str(fees.get("tow_mileage_rate", "0")))
        self.tow_miles_used.setText("0")
        self.tow_hourly_labor_rate.setText(str(fees.get("tow_hourly_labor_rate", "0")))
        self.tow_labor_hours.setText("0")
        self.tow_after_hours_fee.setText(str(fees.get("after_hours_fee", "0")))
        
        # Recovery fees
        self.recovery_handling_fee.setText(str(fees.get("recovery_handling_fee", "0")))
        self.lien_processing_fee.setText(str(fees.get("lien_processing_fee", "0")))
        self.cert_mail_fee.setText(str(fees.get("cert_mail_fee", "0")))
        self.notices_sent.setText("0")
        self.title_search_fee.setText(str(fees.get("title_search_fee", "0")))
        self.dmv_fee.setText(str(fees.get("dmv_fee", "0")))
        self.sale_fee.setText(str(fees.get("sale_fee", "0")))
        
    def create_contract(self):
        """Create a new contract."""
        try:
            customer = Customer(
                name=self.customer_name.text(),
                phone=self.customer_phone.text(),
                address=self.customer_address.text()
            )
            
            # Convert year to int or None
            year_text = self.vehicle_year.text().strip()
            year_value = None
            if year_text:
                try:
                    year_value = int(year_text)
                except ValueError:
                    pass  # Leave as None if invalid
            
            vehicle = Vehicle(
                vehicle_type=self.vehicle_type.currentText(),
                make=self.vehicle_make.text(),
                model=self.vehicle_model.text(),
                year=year_value,
                color=self.vehicle_color.text(),
                plate=self.vehicle_plate.text(),
                vin=self.vehicle_vin.text()
            )
            
            # Map displayed contract type to internal value
            contract_type_map = {
                "Storage": "storage",
                "Tow": "tow",
                "Recovery": "recovery"
            }
            contract_type = contract_type_map.get(self.contract_type.currentText(), "storage")
            
            # Map rate mode
            rate_mode_map = {
                "Daily": "daily",
                "Weekly": "weekly",
                "Monthly": "monthly"
            }
            rate_mode = rate_mode_map.get(self.rate_mode.currentText(), "daily")
            
            # Get storage fees from template (independent values, no formulas)
            vtype = self.vehicle_type.currentText()
            fees = self.fee_templates.get(vtype, {})
            daily_storage_fee = float(fees.get("daily_storage_fee", 0))
            weekly_storage_fee = float(fees.get("weekly_storage_fee", 0))
            monthly_storage_fee = float(fees.get("monthly_storage_fee", 0))
            
            # Create contract with all fields
            contract = StorageContract(
                contract_id=self.storage_data.next_id,
                customer=customer,
                vehicle=vehicle,
                start_date=datetime.today().strftime(DATE_FORMAT),
                contract_type=contract_type,
                rate_mode=rate_mode,
                daily_storage_fee=daily_storage_fee,
                weekly_storage_fee=weekly_storage_fee,
                monthly_storage_fee=monthly_storage_fee,
                admin_fee=float(self.admin_fee.text() or 0),
                # Tow fields
                tow_base_fee=float(self.tow_base_fee.text() or 0),
                tow_mileage_rate=float(self.tow_mileage_rate.text() or 0),
                tow_miles_used=float(self.tow_miles_used.text() or 0),
                tow_hourly_labor_rate=float(self.tow_hourly_labor_rate.text() or 0),
                tow_labor_hours=float(self.tow_labor_hours.text() or 0),
                tow_after_hours_fee=float(self.tow_after_hours_fee.text() or 0),
                # Recovery fields
                recovery_handling_fee=float(self.recovery_handling_fee.text() or 0),
                lien_processing_fee=float(self.lien_processing_fee.text() or 0),
                cert_mail_fee=float(self.cert_mail_fee.text() or 0),
                notices_sent=int(self.notices_sent.text() or 0),
                title_search_fee=float(self.title_search_fee.text() or 0),
                dmv_fee=float(self.dmv_fee.text() or 0),
                sale_fee=float(self.sale_fee.text() or 0),
            )
            
            # Check Florida rules and generate warnings
            warnings = []
            if contract.lien_processing_fee > 250:
                warnings.append(f"⚠️ Lien processing fee ${contract.lien_processing_fee:.2f} exceeds FL maximum of $250")
            
            # Display warnings but don't block creation
            if warnings:
                warning_msg = "Contract created with warnings:\n\n" + "\n".join(warnings)
                QMessageBox.warning(self, "Fee Warnings", warning_msg)
            
            self.storage_data.contracts.append(contract)
            self.storage_data.next_id += 1
            save_data(self.storage_data)
            
            QMessageBox.information(self, "Success", f"Contract #{contract.contract_id} created successfully!")
            self.clear_intake_form()
            self.refresh_contracts()
            self.tabs.setCurrentIndex(0)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create contract: {str(e)}\n\n{traceback.format_exc()}")
            
    def clear_intake_form(self):
        """Clear the intake form."""
        self.customer_name.clear()
        self.customer_phone.clear()
        self.customer_address.clear()
        self.vehicle_make.clear()
        self.vehicle_model.clear()
        self.vehicle_year.clear()
        self.vehicle_color.clear()
        self.vehicle_plate.clear()
        self.vehicle_vin.clear()
        self.rate_mode.setCurrentIndex(0)  # Reset to Daily
        self.tow_miles_used.setText("0")
        self.tow_labor_hours.setText("0")
        self.notices_sent.setText("0")
        self.load_defaults_for_type()
        
    def refresh_fee_table(self):
        """Refresh the fee templates table."""
        self.fee_table.setRowCount(len(self.fee_templates))
        
        for i, (vtype, fees) in enumerate(self.fee_templates.items()):
            # Vehicle type (non-editable)
            vtype_item = QTableWidgetItem(vtype)
            vtype_item.setFlags(vtype_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.fee_table.setItem(i, 0, vtype_item)
            
            # All fee fields (editable)
            self.fee_table.setItem(i, 1, QTableWidgetItem(str(fees.get("daily_storage_fee", "0"))))
            self.fee_table.setItem(i, 2, QTableWidgetItem(str(fees.get("weekly_storage_fee", "0"))))
            self.fee_table.setItem(i, 3, QTableWidgetItem(str(fees.get("monthly_storage_fee", "0"))))
            self.fee_table.setItem(i, 4, QTableWidgetItem(str(fees.get("tow_base_fee", "0"))))
            self.fee_table.setItem(i, 5, QTableWidgetItem(str(fees.get("tow_mileage_rate", "0"))))
            self.fee_table.setItem(i, 6, QTableWidgetItem(str(fees.get("tow_hourly_labor_rate", "0"))))
            self.fee_table.setItem(i, 7, QTableWidgetItem(str(fees.get("after_hours_fee", "0"))))
            self.fee_table.setItem(i, 8, QTableWidgetItem(str(fees.get("recovery_handling_fee", "0"))))
            self.fee_table.setItem(i, 9, QTableWidgetItem(str(fees.get("lien_processing_fee", "0"))))
            self.fee_table.setItem(i, 10, QTableWidgetItem(str(fees.get("cert_mail_fee", "0"))))
            self.fee_table.setItem(i, 11, QTableWidgetItem(str(fees.get("title_search_fee", "0"))))
            self.fee_table.setItem(i, 12, QTableWidgetItem(str(fees.get("dmv_fee", "0"))))
            self.fee_table.setItem(i, 13, QTableWidgetItem(str(fees.get("sale_fee", "0"))))
            self.fee_table.setItem(i, 14, QTableWidgetItem(str(fees.get("admin_fee", "0"))))
            self.fee_table.setItem(i, 15, QTableWidgetItem(str(fees.get("labor_rate", "0"))))
            
    def save_fee_templates_action(self):
        """Save fee templates."""
        try:
            for i in range(self.fee_table.rowCount()):
                vtype = self.fee_table.item(i, 0).text()
                if vtype in self.fee_templates:
                    self.fee_templates[vtype]["daily_storage_fee"] = float(self.fee_table.item(i, 1).text())
                    self.fee_templates[vtype]["weekly_storage_fee"] = float(self.fee_table.item(i, 2).text())
                    self.fee_templates[vtype]["monthly_storage_fee"] = float(self.fee_table.item(i, 3).text())
                    self.fee_templates[vtype]["tow_base_fee"] = float(self.fee_table.item(i, 4).text())
                    self.fee_templates[vtype]["tow_mileage_rate"] = float(self.fee_table.item(i, 5).text())
                    self.fee_templates[vtype]["tow_hourly_labor_rate"] = float(self.fee_table.item(i, 6).text())
                    self.fee_templates[vtype]["after_hours_fee"] = float(self.fee_table.item(i, 7).text())
                    self.fee_templates[vtype]["recovery_handling_fee"] = float(self.fee_table.item(i, 8).text())
                    self.fee_templates[vtype]["lien_processing_fee"] = float(self.fee_table.item(i, 9).text())
                    self.fee_templates[vtype]["cert_mail_fee"] = float(self.fee_table.item(i, 10).text())
                    self.fee_templates[vtype]["title_search_fee"] = float(self.fee_table.item(i, 11).text())
                    self.fee_templates[vtype]["dmv_fee"] = float(self.fee_table.item(i, 12).text())
                    self.fee_templates[vtype]["sale_fee"] = float(self.fee_table.item(i, 13).text())
                    self.fee_templates[vtype]["admin_fee"] = float(self.fee_table.item(i, 14).text())
                    self.fee_templates[vtype]["labor_rate"] = float(self.fee_table.item(i, 15).text())
                    
            save_fee_templates(self.fee_templates)
            QMessageBox.information(self, "Success", "Fee templates saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save fee templates: {str(e)}")
            
    def print_record(self):
        """Print a contract record."""
        print("Print record called!")  # Debug
        QMessageBox.information(self, "Print", "Print functionality coming soon!")
        
    def export_summary(self):
        """Export contract summary."""
        QMessageBox.information(self, "Export", "Export functionality coming soon!")
        
    def copy_summary(self):
        """Copy summary to clipboard."""
        QApplication.clipboard().setText(self.summary_text.toPlainText())
        self.status_label.setText("Summary copied to clipboard")
        
    def show_settings(self):
        """Show settings dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        
        # Theme selection
        theme_label = QLabel("Color Scheme:")
        theme_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(theme_label)
        
        theme_group = QButtonGroup(dialog)
        for theme_name in THEMES.keys():
            rb = QRadioButton(theme_name)
            if theme_name == self.current_theme:
                rb.setChecked(True)
            rb.clicked.connect(lambda checked, t=theme_name: self.apply_theme(t))
            theme_group.addButton(rb)
            layout.addWidget(rb)
            
        layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
        
    def toggle_theme(self):
        """Toggle between Dark and Light themes."""
        new_theme = "Light" if self.current_theme == "Dark" else "Dark"
        self.apply_theme(new_theme)
        self.save_theme_preference(new_theme)
    
    def show_help(self):
        """Show help dialog."""
        QMessageBox.information(self, "Help", 
                               "Storage & Recovery Lot Help\n\n"
                               "Use the Intake tab to create new contracts.\n"
                               "Use the Contracts tab to view and manage existing contracts.\n"
                               "Use the Fee Templates tab to manage default fees.")
    
    def show_documentation(self):
        """Show documentation dialog."""
        QMessageBox.information(self, "Documentation", 
                               "For full documentation, please see the README.md file.")
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About", 
                         "Storage & Recovery Lot\nVersion 2.0\nPyQt6 Edition")
        
    def apply_theme(self, theme_name: str):
        """Apply a color theme."""
        if theme_name not in THEMES:
            return
            
        self.current_theme = theme_name
        colors = THEMES[theme_name]
        
        # Update title bar
        self.title_bar.theme_colors = colors
        self.title_bar.setup_ui()
        
        # Build stylesheet
        stylesheet = f"""
            QMainWindow, QWidget {{
                background-color: {colors['bg']};
                color: {colors['fg']};
            }}
            QTabWidget::pane {{
                border: none;
                background: {colors['frame_bg']};
            }}
            QTabBar::tab {{
                background: {colors['tree_even']};
                color: {colors['fg']};
                padding: 12px 24px;
                border: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                border-bottom: 2px solid transparent;
            }}
            QTabBar::tab:selected {{
                background: {colors['frame_bg']};
                border-bottom: 2px solid {colors['accent']};
                font-weight: bold;
            }}
            QTabBar::tab:hover {{
                background: {colors['button_hover']};
            }}
            QTableWidget {{
                background-color: {colors['tree_odd']};
                alternate-background-color: {colors['tree_even']};
                color: {colors['fg']};
                gridline-color: {colors['border']};
                selection-background-color: {colors['select_bg']};
                selection-color: {colors['select_fg']};
            }}
            QHeaderView::section {{
                background-color: {colors['button_bg']};
                color: {colors['button_fg']};
                padding: 5px;
                border: 1px solid {colors['border']};
                font-weight: bold;
            }}
            QPushButton {{
                background-color: {colors['button_bg']};
                color: {colors['button_fg']};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {colors['button_hover']};
            }}
            QPushButton:pressed {{
                background-color: {colors['select_bg']};
            }}
            QLineEdit, QTextEdit, QComboBox {{
                background-color: {colors['entry_bg']};
                color: {colors['entry_fg']};
                border: 1px solid {colors['border']};
                padding: 6px;
                border-radius: 4px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border: 2px solid {colors['accent']};
            }}
            QLabel {{
                color: {colors['fg']};
            }}
            QMenu {{
                background-color: {colors['entry_bg']};
                color: {colors['fg']};
                border: 1px solid {colors['border']};
            }}
            QMenu::item:selected {{
                background-color: {colors['select_bg']};
            }}
        """
        
        self.setStyleSheet(stylesheet)
        self.save_theme_preference()
        
    def load_theme_preference(self):
        """Load saved theme preference."""
        try:
            theme_file = Path(__file__).parent / "theme_preference.txt"
            if theme_file.exists():
                saved = theme_file.read_text().strip()
                if saved in THEMES:
                    self.current_theme = saved
        except Exception:
            pass
            
    def save_theme_preference(self):
        """Save current theme preference."""
        try:
            theme_file = Path(__file__).parent / "theme_preference.txt"
            theme_file.write_text(self.current_theme)
        except Exception:
            pass


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for consistency
    
    window = LotAppQt()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
