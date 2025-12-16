"""PyQt6 UI for the Storage & Recovery Lot program."""
from __future__ import annotations

import sys
import traceback
import csv
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
    lien_timeline, past_due_status,
    record_payment, storage_days,
)
from lot_models import Customer, Vehicle, StorageContract, StorageData, DATE_FORMAT
from persistence import load_data, save_data, load_fee_templates, save_fee_templates
from config import ENABLE_INVOLUNTARY_TOWS, MAX_ADMIN_FEE, MAX_LIEN_FEE, TOW_STORAGE_EXEMPTION_HOURS
from theme_config import get_theme_colors, get_application_stylesheet


class CustomTitleBar(QWidget):
    """Custom title bar with menu bar and window controls."""
    """Custom title bar with window controls."""
    
    close_clicked = pyqtSignal()
    minimize_clicked = pyqtSignal()
    maximize_clicked = pyqtSignal()
    
    def __init__(self, parent=None, theme_colors=None):
        super().__init__(parent)
        from theme_config import get_theme_colors
        self.theme_colors = theme_colors if theme_colors else get_theme_colors("Dark")
        self.drag_position = QPoint()
        self.menu_callbacks = {}  # Store menu callbacks
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the title bar UI."""
        self.setFixedHeight(40)
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet(f"""
            CustomTitleBar {{
                background-color: {self.theme_colors['titlebar_bg']};
                color: {self.theme_colors['titlebar_fg']};
                border: none;
                margin: 0px;
                padding: 0px;
            }}
            QWidget {{
                background-color: {self.theme_colors['titlebar_bg']};
                color: {self.theme_colors['titlebar_fg']};
                border: none;
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
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging."""
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_position'):
            self.window().move(event.globalPosition().toPoint() - self.drag_position)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if hasattr(self, 'drag_position'):
            delattr(self, 'drag_position')


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
        
        # Resizing variables
        self.resizing = False
        self.resize_edge = None
        self.resize_start_pos = None
        self.resize_start_geometry = None
        self.resize_margin = 10
        self.current_cursor_edge = None  # Track which edge cursor is showing
        
        self.init_ui()
        self.load_theme_preference()
        self.apply_theme(self.current_theme)
        
        # Check for urgent items on startup
        self.check_urgent_alerts()
        
        # Enable mouse tracking for resize detection
        self.setMouseTracking(True)
        
        # Install event filter on application to capture ALL mouse events globally
        QApplication.instance().installEventFilter(self)
        
    def init_ui(self):
        """Initialize the user interface."""
        # Frameless window for custom title bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setGeometry(100, 100, 1200, 700)
        self.setMinimumSize(800, 600)
        
        # Central widget
        central_widget = QWidget()
        central_widget.setStyleSheet("border: none; margin: 0; padding: 0;")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Custom title bar
        self.title_bar = CustomTitleBar(self, get_theme_colors(self.current_theme))
        self.title_bar.close_clicked.connect(self.close)
        self.title_bar.minimize_clicked.connect(self.showMinimized)
        self.title_bar.maximize_clicked.connect(self.toggle_maximize)
        main_layout.addWidget(self.title_bar)
        main_layout.setSpacing(0)  # Ensure no spacing between title bar and content
        
        # Create menus as instance variables
        self.file_menu = QMenu(self)
        
        backup_action = QAction("Backup Data...", self)
        backup_action.triggered.connect(self.backup_data)
        self.file_menu.addAction(backup_action)
        
        restore_action = QAction("Restore from Backup...", self)
        restore_action.triggered.connect(self.restore_data)
        self.file_menu.addAction(restore_action)
        
        self.file_menu.addSeparator()
        
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
        
        alerts_action = QAction("🔔 Check for Urgent Alerts", self)
        alerts_action.triggered.connect(self.manual_alert_check)
        self.help_menu.addAction(alerts_action)
        
        self.help_menu.addSeparator()
        
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
        content_widget.setStyleSheet(f"border: none; background-color: {get_theme_colors(self.current_theme)['titlebar_bg']}; margin-top: 0px; padding-top: 0px;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        main_layout.addWidget(content_widget, 0)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(False)
        content_layout.addWidget(self.tabs, 0)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("padding: 5px;")
        content_layout.addWidget(self.status_label)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_contracts_tab()
        self.create_intake_tab()
        self.create_reports_tab()
        self.create_fee_tab()
    
    def create_dashboard_tab(self):
        """Create the dashboard overview tab."""
        dashboard_widget = QWidget()
        layout = QVBoxLayout(dashboard_widget)
        layout.setSpacing(15)
        
        # Dashboard title
        title = QLabel("📊 Dashboard Overview")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("padding: 10px; color: #0078d4;")
        layout.addWidget(title)
        
        # Calculate statistics
        total_contracts = len(self.storage_data.contracts)
        active_contracts = sum(1 for c in self.storage_data.contracts if c.status != "Paid")
        total_revenue = sum(balance(c, include_breakdown=False) for c in self.storage_data.contracts)
        total_paid = sum(sum(p.amount for p in c.payments) for c in self.storage_data.contracts)
        outstanding = sum(balance(c, include_breakdown=False) for c in self.storage_data.contracts if balance(c) > 0)
        
        # Count by type
        storage_count = sum(1 for c in self.storage_data.contracts if c.contract_type.lower() == "storage")
        tow_count = sum(1 for c in self.storage_data.contracts if c.contract_type.lower() == "tow")
        recovery_count = sum(1 for c in self.storage_data.contracts if c.contract_type.lower() == "recovery")
        
        # Past due contracts
        past_due_contracts = [c for c in self.storage_data.contracts if past_due_status(c)[0]]
        past_due_count = len(past_due_contracts)
        past_due_amount = sum(balance(c) for c in past_due_contracts)
        
        # Lien eligible contracts
        lien_eligible_contracts = [c for c in self.storage_data.contracts if lien_eligibility(c)[0]]
        lien_eligible_count = len(lien_eligible_contracts)
        
        # Sale eligible contracts
        sale_eligible_contracts = [c for c in self.storage_data.contracts 
                                   if lien_timeline(c).get("is_sale_eligible", False)]
        sale_eligible_count = len(sale_eligible_contracts)
        
        # Summary cards row
        cards_layout = QHBoxLayout()
        
        # Card 1: Total Contracts
        card1 = self.create_stat_card("Total Contracts", str(total_contracts), 
                                      f"{active_contracts} active", "#0078d4")
        cards_layout.addWidget(card1)
        
        # Card 2: Revenue
        card2 = self.create_stat_card("Total Revenue", f"${total_paid:,.2f}", 
                                      f"${outstanding:,.2f} outstanding", "#2e7d32")
        cards_layout.addWidget(card2)
        
        # Card 3: Past Due
        color3 = "#c62828" if past_due_count > 0 else "#757575"
        card3 = self.create_stat_card("Past Due", str(past_due_count), 
                                      f"${past_due_amount:,.2f}" if past_due_count > 0 else "All current",
                                      color3)
        cards_layout.addWidget(card3)
        
        # Card 4: Lien Eligible
        color4 = "#e65100" if lien_eligible_count > 0 else "#757575"
        card4 = self.create_stat_card("Lien Eligible", str(lien_eligible_count),
                                      f"{sale_eligible_count} sale eligible", color4)
        cards_layout.addWidget(card4)
        
        layout.addLayout(cards_layout)
        
        # Contract type breakdown
        breakdown_label = QLabel("Contract Type Breakdown")
        breakdown_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        breakdown_label.setStyleSheet("padding-top: 10px;")
        layout.addWidget(breakdown_label)
        
        breakdown_layout = QHBoxLayout()
        
        # Storage
        storage_revenue = sum(balance(c, include_breakdown=False) for c in self.storage_data.contracts 
                            if c.contract_type.lower() == "storage")
        storage_widget = self.create_type_card("Storage Contracts", storage_count, 
                                              storage_revenue, "#0078d4")
        breakdown_layout.addWidget(storage_widget)
        
        # Tow
        tow_revenue = sum(balance(c, include_breakdown=False) for c in self.storage_data.contracts 
                         if c.contract_type.lower() == "tow")
        tow_widget = self.create_type_card("Tow Contracts", tow_count, 
                                          tow_revenue, "#2e7d32")
        breakdown_layout.addWidget(tow_widget)
        
        # Recovery
        recovery_revenue = sum(balance(c, include_breakdown=False) for c in self.storage_data.contracts 
                              if c.contract_type.lower() == "recovery")
        recovery_widget = self.create_type_card("Recovery Contracts", recovery_count, 
                                               recovery_revenue, "#c62828")
        breakdown_layout.addWidget(recovery_widget)
        
        layout.addLayout(breakdown_layout)
        
        # Upcoming deadlines section
        deadline_label = QLabel("⚠️ Upcoming Deadlines (Next 7 Days)")
        deadline_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        deadline_label.setStyleSheet("padding-top: 10px; color: #c62828;")
        layout.addWidget(deadline_label)
        
        # Find contracts with upcoming deadlines
        upcoming = []
        today = datetime.today()
        
        for contract in self.storage_data.contracts:
            timeline = lien_timeline(contract)
            
            # Check various deadline dates
            for key, date_str in timeline.items():
                if date_str and key.endswith('_date') or key.endswith('_due'):
                    try:
                        deadline_date = datetime.strptime(date_str, "%Y-%m-%d")
                        days_until = (deadline_date - today).days
                        
                        if 0 <= days_until <= 7:
                            upcoming.append({
                                'contract_id': contract.contract_id,
                                'customer': contract.customer.name,
                                'vehicle': f"{contract.vehicle.vehicle_type} {contract.vehicle.plate}",
                                'deadline': key.replace('_', ' ').title(),
                                'date': date_str,
                                'days': days_until
                            })
                    except:
                        pass
        
        if upcoming:
            # Sort by days until deadline
            upcoming.sort(key=lambda x: x['days'])
            
            # Create table for upcoming items
            deadline_table = QTableWidget()
            deadline_table.setColumnCount(5)
            deadline_table.setHorizontalHeaderLabels(['ID', 'Customer', 'Vehicle', 'Deadline Type', 'Days'])
            deadline_table.setRowCount(min(len(upcoming), 10))  # Show max 10
            deadline_table.setMaximumHeight(250)
            
            for i, item in enumerate(upcoming[:10]):
                deadline_table.setItem(i, 0, QTableWidgetItem(str(item['contract_id'])))
                deadline_table.setItem(i, 1, QTableWidgetItem(item['customer']))
                deadline_table.setItem(i, 2, QTableWidgetItem(item['vehicle']))
                deadline_table.setItem(i, 3, QTableWidgetItem(item['deadline']))
                
                days_item = QTableWidgetItem(f"{item['days']} days" if item['days'] > 0 else "TODAY!")
                if item['days'] == 0:
                    days_item.setForeground(QColor("#c62828"))
                    days_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                deadline_table.setItem(i, 4, days_item)
            
            deadline_table.horizontalHeader().setStretchLastSection(True)
            layout.addWidget(deadline_table)
        else:
            no_deadlines = QLabel("✓ No urgent deadlines in the next 7 days")
            no_deadlines.setStyleSheet("color: #2e7d32; padding: 10px; font-style: italic;")
            layout.addWidget(no_deadlines)
        
        # Quick actions
        actions_label = QLabel("Quick Actions")
        actions_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        actions_label.setStyleSheet("padding-top: 10px;")
        layout.addWidget(actions_label)
        
        actions_layout = QHBoxLayout()
        
        new_contract_btn = QPushButton("➕ New Contract")
        new_contract_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(2))  # Switch to intake tab
        new_contract_btn.setMinimumHeight(40)
        actions_layout.addWidget(new_contract_btn)
        
        export_btn = QPushButton("📊 Export Data")
        export_btn.clicked.connect(self.export_to_csv)
        export_btn.setMinimumHeight(40)
        actions_layout.addWidget(export_btn)
        
        backup_btn = QPushButton("💾 Backup Data")
        backup_btn.clicked.connect(self.backup_data)
        backup_btn.setMinimumHeight(40)
        actions_layout.addWidget(backup_btn)
        
        refresh_btn = QPushButton("🔄 Refresh Dashboard")
        refresh_btn.clicked.connect(self.refresh_dashboard)
        refresh_btn.setMinimumHeight(40)
        actions_layout.addWidget(refresh_btn)
        
        layout.addLayout(actions_layout)
        
        layout.addStretch()
        
        self.tabs.addTab(dashboard_widget, "Dashboard")
        self.update_notification_badge()
    
    def update_notification_badge(self):
        """Update tab text with notification badge if urgent items exist."""
        urgent_count = self.count_urgent_items()
        if urgent_count > 0:
            self.tabs.setTabText(0, f"Dashboard ({urgent_count})")
            self.tabs.tabBar().setTabTextColor(0, QColor("#c62828"))
        else:
            self.tabs.setTabText(0, "Dashboard")
            self.tabs.tabBar().setTabTextColor(0, QColor("#000000"))
    
    def count_urgent_items(self):
        """Count contracts with urgent deadlines (today or overdue)."""
        urgent_count = 0
        today = datetime.today()
        
        for contract in self.storage_data.contracts:
            # Skip paid contracts
            if balance(contract) == 0:
                continue
            
            timeline = lien_timeline(contract)
            
            # Check all deadline dates
            for key, date_str in timeline.items():
                if date_str and (key.endswith('_date') or key.endswith('_due')):
                    try:
                        deadline_date = datetime.strptime(date_str, "%Y-%m-%d")
                        days_until = (deadline_date - today).days
                        
                        # Count if today or overdue
                        if days_until <= 0:
                            urgent_count += 1
                            break  # Only count each contract once
                    except:
                        pass
        
        return urgent_count
    
    def check_urgent_alerts(self):
        """Check for urgent items and show alert dialog on startup."""
        urgent_items = []
        today = datetime.today()
        
        for contract in self.storage_data.contracts:
            # Skip paid contracts
            if balance(contract) == 0:
                continue
            
            timeline = lien_timeline(contract)
            contract_alerts = []
            
            # Check all deadline dates
            for key, date_str in timeline.items():
                if date_str and (key.endswith('_date') or key.endswith('_due')):
                    try:
                        deadline_date = datetime.strptime(date_str, "%Y-%m-%d")
                        days_until = (deadline_date - today).days
                        
                        # Alert if today or overdue
                        if days_until <= 0:
                            status = "TODAY!" if days_until == 0 else f"{abs(days_until)} days OVERDUE"
                            contract_alerts.append({
                                'deadline': key.replace('_', ' ').title(),
                                'date': date_str,
                                'status': status
                            })
                    except:
                        pass
            
            if contract_alerts:
                urgent_items.append({
                    'contract_id': contract.contract_id,
                    'customer': contract.customer.name,
                    'vehicle': f"{contract.vehicle.vehicle_type} {contract.vehicle.plate}",
                    'balance': balance(contract),
                    'alerts': contract_alerts
                })
        
        # Show alert dialog if urgent items exist
        if urgent_items:
            self.show_urgent_alerts_dialog(urgent_items)
    
    def show_urgent_alerts_dialog(self, urgent_items):
        """Display dialog with urgent items requiring attention."""
        dialog = QDialog(self)
        dialog.setWindowTitle("⚠️ Urgent Items Requiring Attention")
        dialog.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(dialog)
        
        # Warning header
        header = QLabel(f"🚨 {len(urgent_items)} contract(s) have urgent deadlines TODAY or OVERDUE!")
        header.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header.setStyleSheet("color: #c62828; padding: 10px; background-color: #ffebee; border-radius: 5px;")
        layout.addWidget(header)
        
        # Scrollable list of urgent items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        for item in urgent_items:
            item_frame = QFrame()
            item_frame.setFrameStyle(QFrame.Shape.Box)
            item_frame.setStyleSheet("border: 2px solid #c62828; border-radius: 5px; padding: 10px; margin: 5px;")
            item_layout = QVBoxLayout(item_frame)
            
            # Contract info
            info_label = QLabel(f"<b>Contract #{item['contract_id']}</b> - {item['customer']}")
            info_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            item_layout.addWidget(info_label)
            
            vehicle_label = QLabel(f"Vehicle: {item['vehicle']} | Balance: ${item['balance']:.2f}")
            item_layout.addWidget(vehicle_label)
            
            # Alerts
            for alert in item['alerts']:
                alert_label = QLabel(f"  ⚠️ {alert['deadline']}: {alert['date']} - <b>{alert['status']}</b>")
                alert_label.setStyleSheet("color: #c62828;")
                item_layout.addWidget(alert_label)
            
            scroll_layout.addWidget(item_frame)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        view_contracts_btn = QPushButton("View Contracts")
        view_contracts_btn.clicked.connect(lambda: (dialog.accept(), self.tabs.setCurrentIndex(1)))
        btn_layout.addWidget(view_contracts_btn)
        
        close_btn = QPushButton("Dismiss")
        close_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.exec()
    
    def create_stat_card(self, title, value, subtitle, color):
        """Create a statistic card widget."""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setLineWidth(2)
        card.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {color};
                border-radius: 8px;
                background-color: #ffffff;
                padding: 15px;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11px;")
        card_layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {color};")
        card_layout.addWidget(value_label)
        
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet("color: #757575; font-size: 10px;")
        card_layout.addWidget(subtitle_label)
        
        return card
    
    def create_type_card(self, title, count, revenue, color):
        """Create a contract type breakdown card."""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet(f"""
            QFrame {{
                border: 1px solid {color};
                border-radius: 5px;
                background-color: #f9f9f9;
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        layout.addWidget(title_label)
        
        count_label = QLabel(f"Count: {count}")
        layout.addWidget(count_label)
        
        revenue_label = QLabel(f"Revenue: ${revenue:,.2f}")
        revenue_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(revenue_label)
        
        return card
    
    def refresh_dashboard(self):
        """Refresh the dashboard with current data."""
        # Store current tab to restore after refresh
        current_tab = self.tabs.currentIndex()
        
        # Remove the first tab (Contracts overview)
        self.tabs.removeTab(0)
        
        # Recreate dashboard
        dashboard_widget = QWidget()
        layout = QVBoxLayout(dashboard_widget)
        layout.setSpacing(15)
        
        # Dashboard title
        title = QLabel("📊 Dashboard Overview")
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Load current data
        data = load_data()
        
        # Stats section
        stats_frame = QFrame()
        stats_frame.setStyleSheet("padding: 10px; border: 1px solid #ddd; border-radius: 5px;")
        stats_layout = QHBoxLayout(stats_frame)
        
        total_contracts = len(data.contracts)
        active_contracts = sum(1 for c in data.contracts if balance(c, datetime.today()) > 0)
        
        total_label = QLabel(f"<b>Total Contracts:</b> {total_contracts}")
        total_label.setStyleSheet("font-size: 14px; padding: 5px;")
        active_label = QLabel(f"<b>Active Contracts:</b> {active_contracts}")
        active_label.setStyleSheet("font-size: 14px; padding: 5px;")
        
        stats_layout.addWidget(total_label)
        stats_layout.addWidget(active_label)
        stats_layout.addStretch()
        
        layout.addWidget(stats_frame)
        
        # Urgent items section
        urgent_label = QLabel("⚠️ Urgent Items")
        urgent_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px; margin-top: 10px;")
        layout.addWidget(urgent_label)
        
        urgent_table = QTableWidget()
        urgent_table.setColumnCount(4)
        urgent_table.setHorizontalHeaderLabels(["Contract ID", "Type", "Vehicle", "Action Needed"])
        urgent_table.horizontalHeader().setStretchLastSection(True)
        
        # Find urgent items
        today = datetime.today()
        urgent_items = []
        for contract in data.contracts:
            if balance(contract, today) > 0:
                timeline = lien_timeline(contract)
                # Check for urgent dates
                for key, value in timeline.items():
                    if isinstance(value, datetime):
                        if value.date() <= today.date():
                            urgent_items.append({
                                "contract_id": contract.contract_id,
                                "type": contract.contract_type,
                                "vehicle": f"{contract.vehicle.year} {contract.vehicle.make} {contract.vehicle.model}",
                                "action": key.replace("_", " ").title()
                            })
        
        urgent_table.setRowCount(len(urgent_items))
        for i, item in enumerate(urgent_items):
            urgent_table.setItem(i, 0, QTableWidgetItem(item["contract_id"]))
            urgent_table.setItem(i, 1, QTableWidgetItem(item["type"]))
            urgent_table.setItem(i, 2, QTableWidgetItem(item["vehicle"]))
            urgent_table.setItem(i, 3, QTableWidgetItem(item["action"]))
        
        layout.addWidget(urgent_table)
        
        # Quick actions
        actions_label = QLabel("⚡ Quick Actions")
        actions_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px; margin-top: 10px;")
        layout.addWidget(actions_label)
        
        actions_layout = QHBoxLayout()
        
        new_storage_btn = QPushButton("New Storage Contract")
        new_tow_btn = QPushButton("New Tow Contract")
        view_all_btn = QPushButton("View All Contracts")
        
        new_storage_btn.clicked.connect(lambda: (self.tabs.setCurrentIndex(2), self.intake_type_combo.setCurrentText("Storage")))
        new_tow_btn.clicked.connect(lambda: (self.tabs.setCurrentIndex(2), self.intake_type_combo.setCurrentText("Tow")))
        view_all_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        
        actions_layout.addWidget(new_storage_btn)
        actions_layout.addWidget(new_tow_btn)
        actions_layout.addWidget(view_all_btn)
        
        layout.addLayout(actions_layout)
        layout.addStretch()
        
        # Insert at position 0
        self.tabs.insertTab(0, dashboard_widget, "Dashboard")
        
        # Restore current tab or set to dashboard
        if current_tab == 0:
            self.tabs.setCurrentIndex(0)
        else:
            self.tabs.setCurrentIndex(current_tab)
            
        self.update_notification_badge()
        self.status_label.setText("Dashboard refreshed")

    
    def create_contracts_tab(self):
        """Create the contracts list tab."""
        contracts_widget = QWidget()
        layout = QVBoxLayout(contracts_widget)
        
        # Filter section
        filter_frame = QFrame()
        filter_frame.setFrameStyle(QFrame.Shape.Box)
        filter_frame.setStyleSheet("padding: 10px; border: 1px solid #ddd; border-radius: 5px;")
        filter_layout = QVBoxLayout(filter_frame)
        
        # Filter title
        filter_title = QLabel("🔍 Filters & Search")
        filter_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        filter_layout.addWidget(filter_title)
        
        # First row: Search and Type filter
        row1_layout = QHBoxLayout()
        
        # Enhanced search
        search_label = QLabel("Search:")
        row1_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Customer, Phone, Vehicle, Plate, VIN...")
        self.search_input.textChanged.connect(self.apply_filters)
        self.search_input.setMinimumWidth(300)
        row1_layout.addWidget(self.search_input)
        
        # Contract type filter
        type_label = QLabel("Type:")
        row1_layout.addWidget(type_label)
        
        self.type_filter = QComboBox()
        type_filter_items = ["All Types", "Storage", "Tow"]
        if ENABLE_INVOLUNTARY_TOWS:
            type_filter_items.append("Recovery")
        self.type_filter.addItems(type_filter_items)
        self.type_filter.currentTextChanged.connect(self.apply_filters)
        row1_layout.addWidget(self.type_filter)
        
        # Status filter
        status_label = QLabel("Status:")
        row1_layout.addWidget(status_label)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Status", "Active", "Paid", "Past Due", "Lien Eligible", "Sale Eligible"])
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        row1_layout.addWidget(self.status_filter)
        
        row1_layout.addStretch()
        filter_layout.addLayout(row1_layout)
        
        # Second row: Date range filter
        row2_layout = QHBoxLayout()
        
        date_label = QLabel("Date Range:")
        row2_layout.addWidget(date_label)
        
        self.date_from = QLineEdit()
        self.date_from.setPlaceholderText("From: YYYY-MM-DD")
        self.date_from.setMaximumWidth(120)
        self.date_from.textChanged.connect(self.apply_filters)
        row2_layout.addWidget(self.date_from)
        
        to_label = QLabel("to")
        row2_layout.addWidget(to_label)
        
        self.date_to = QLineEdit()
        self.date_to.setPlaceholderText("To: YYYY-MM-DD")
        self.date_to.setMaximumWidth(120)
        self.date_to.textChanged.connect(self.apply_filters)
        row2_layout.addWidget(self.date_to)
        
        # Clear filters button
        clear_btn = QPushButton("Clear All Filters")
        clear_btn.clicked.connect(self.clear_filters)
        row2_layout.addWidget(clear_btn)
        
        # Active filter count
        self.filter_count_label = QLabel("")
        self.filter_count_label.setStyleSheet("color: #0078d4; font-weight: bold;")
        row2_layout.addWidget(self.filter_count_label)
        
        row2_layout.addStretch()
        filter_layout.addLayout(row2_layout)
        
        layout.addWidget(filter_frame)
        
        # Contract table
        self.contract_table = QTableWidget()
        self.contract_table.setColumnCount(9)
        self.contract_table.setHorizontalHeaderLabels([
            "ID", "Customer", "Vehicle", "Type", "Start Date", "Balance", "Days", "Next Milestone", "Status"
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
        
        payment_btn = QPushButton("Record Payment")
        payment_btn.clicked.connect(self.record_payment)
        btn_layout.addWidget(payment_btn)
        
        lien_btn = QPushButton("Generate Lien Notice")
        lien_btn.clicked.connect(self.generate_lien_notice)
        btn_layout.addWidget(lien_btn)
        
        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_to_csv)
        btn_layout.addWidget(export_btn)
        
        print_btn = QPushButton("Print Summary")
        print_btn.clicked.connect(self.print_contract_summary)
        btn_layout.addWidget(print_btn)
        
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
        # Only show Recovery if involuntary towing is enabled (requires wrecker license)
        contract_types = ["Storage", "Tow"]
        if ENABLE_INVOLUNTARY_TOWS:
            contract_types.append("Recovery")
        self.contract_type.addItems(contract_types)
        self.contract_type.currentTextChanged.connect(self.on_contract_type_changed)
        form_layout.addRow("Contract Type:", self.contract_type)
        
        form_layout.addRow(QLabel(""))  # Spacer
        
        # Customer fields
        self.customer_name = QLineEdit()
        self.customer_phone = QLineEdit()
        self.customer_phone.setPlaceholderText("(555) 123-4567")
        self.customer_phone.textChanged.connect(self.format_phone_number)
        self.customer_address = QLineEdit()
        
        # Required field labels
        name_label = QLabel("Customer Name: *")
        name_label.setStyleSheet("font-weight: bold;")
        phone_label = QLabel("Phone: *")
        phone_label.setStyleSheet("font-weight: bold;")
        
        form_layout.addRow(name_label, self.customer_name)
        form_layout.addRow(phone_label, self.customer_phone)
        form_layout.addRow("Address:", self.customer_address)
        
        # Phone validation warning
        self.phone_warning = QLabel("")
        self.phone_warning.setStyleSheet("color: #d32f2f; font-size: 10px;")
        form_layout.addRow("", self.phone_warning)
        
        form_layout.addRow(QLabel(""))  # Spacer
        
        # Vehicle fields
        self.vehicle_type = QComboBox()
        self.vehicle_type.addItems(list(self.fee_templates.keys()))
        self.vehicle_type.currentTextChanged.connect(self.load_defaults_for_type)
        form_layout.addRow("Vehicle Type:", self.vehicle_type)
        
        self.vehicle_make = QLineEdit()
        self.vehicle_model = QLineEdit()
        self.vehicle_year = QLineEdit()
        self.vehicle_year.setPlaceholderText("2020")
        self.vehicle_color = QLineEdit()
        self.vehicle_plate = QLineEdit()
        self.vehicle_plate.setPlaceholderText("ABC1234")
        self.vehicle_plate.textChanged.connect(self.format_license_plate)
        self.vehicle_vin = QLineEdit()
        self.vehicle_vin.setPlaceholderText("17 characters")
        self.vehicle_vin.setMaxLength(17)
        self.vehicle_vin.textChanged.connect(self.validate_vin)
        
        # Required field labels for vehicle
        plate_label = QLabel("License Plate: *")
        plate_label.setStyleSheet("font-weight: bold;")
        
        form_layout.addRow("Make:", self.vehicle_make)
        form_layout.addRow("Model:", self.vehicle_model)
        form_layout.addRow("Year:", self.vehicle_year)
        form_layout.addRow("Color:", self.vehicle_color)
        form_layout.addRow(plate_label, self.vehicle_plate)
        form_layout.addRow("VIN:", self.vehicle_vin)
        
        # VIN validation warning
        self.vin_warning = QLabel("")
        self.vin_warning.setStyleSheet("color: #d32f2f; font-size: 10px;")
        form_layout.addRow("", self.vin_warning)
        
        form_layout.addRow(QLabel(""))  # Spacer
        
        # Storage rate mode (all contract types)
        self.rate_mode = QComboBox()
        self.rate_mode.addItems(["Daily", "Weekly", "Monthly"])
        form_layout.addRow("Storage Rate Mode:", self.rate_mode)
        
        form_layout.addRow(QLabel(""))  # Spacer
        
        # Storage fees section
        storage_section = QLabel("=== Storage Fees (All Contracts) ===")
        storage_section.setStyleSheet("font-weight: bold; color: #0078d4;")
        form_layout.addRow(storage_section)
        
        self.daily_storage_fee = QLineEdit()
        self.weekly_storage_fee = QLineEdit()
        self.monthly_storage_fee = QLineEdit()
        
        form_layout.addRow("Daily Storage Fee:", self.daily_storage_fee)
        form_layout.addRow("Weekly Storage Fee:", self.weekly_storage_fee)
        form_layout.addRow("Monthly Storage Fee:", self.monthly_storage_fee)
        
        form_layout.addRow(QLabel(""))  # Spacer
        
        # Common fields
        common_section = QLabel("=== Common Fees ===")
        common_section.setStyleSheet("font-weight: bold; color: #0078d4;")
        form_layout.addRow(common_section)
        
        self.admin_fee = QLineEdit()
        self.admin_fee.textChanged.connect(self.validate_admin_fee)
        self.admin_fee_warning = QLabel("")
        self.admin_fee_warning.setStyleSheet("color: #d32f2f; font-weight: bold;")
        form_layout.addRow("Admin Fee (max $250):", self.admin_fee)
        form_layout.addRow("", self.admin_fee_warning)
        
        # Tow-specific fields
        self.tow_section_label = QLabel("=== Tow Fees (Voluntary Customer-Authorized) ===")
        self.tow_section_label.setStyleSheet("font-weight: bold; color: #2e7d32;")
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
        self.recovery_section_label = QLabel("=== Recovery Fees (Involuntary - FL 713.78) ===")
        self.recovery_section_label.setStyleSheet("font-weight: bold; color: #c62828;")
        form_layout.addRow(self.recovery_section_label)
        
        self.recovery_handling_fee = QLineEdit()
        self.lien_processing_fee = QLineEdit()
        self.lien_processing_fee.textChanged.connect(self.validate_lien_fee)
        self.cert_mail_fee = QLineEdit()
        self.notices_sent = QLineEdit()
        self.title_search_fee = QLineEdit()
        self.dmv_fee = QLineEdit()
        self.sale_fee = QLineEdit()
        
        form_layout.addRow("Recovery Handling Fee:", self.recovery_handling_fee)
        form_layout.addRow("Lien Processing Fee (max $250):", self.lien_processing_fee)
        self.lien_fee_warning = QLabel("")
        self.lien_fee_warning.setStyleSheet("color: #d32f2f; font-weight: bold;")
        form_layout.addRow("", self.lien_fee_warning)
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
            self.lien_fee_warning,
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
        
    def create_reports_tab(self):
        """Create the reports tab with financial summaries."""
        reports_widget = QWidget()
        layout = QVBoxLayout(reports_widget)
        layout.setSpacing(15)
        
        # Reports title
        title = QLabel("📊 Financial Reports & Analysis")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("padding: 10px; color: #0078d4;")
        layout.addWidget(title)
        
        # Report selector
        selector_layout = QHBoxLayout()
        selector_label = QLabel("Select Report:")
        selector_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        selector_layout.addWidget(selector_label)
        
        self.report_selector = QComboBox()
        self.report_selector.addItems([
            "Monthly Revenue Summary",
            "Aging Analysis (30/60/90+ Days)",
            "Customer History",
            "Year-End Tax Summary"
        ])
        self.report_selector.currentTextChanged.connect(self.generate_selected_report)
        selector_layout.addWidget(self.report_selector)
        
        generate_btn = QPushButton("Generate Report")
        generate_btn.clicked.connect(self.generate_selected_report)
        selector_layout.addWidget(generate_btn)
        
        export_report_btn = QPushButton("Export Report")
        export_report_btn.clicked.connect(self.export_current_report)
        selector_layout.addWidget(export_report_btn)
        
        selector_layout.addStretch()
        layout.addLayout(selector_layout)
        
        # Report display area
        self.report_display = QTextEdit()
        self.report_display.setReadOnly(True)
        self.report_display.setFontFamily("Courier New")
        layout.addWidget(self.report_display)
        
        self.tabs.addTab(reports_widget, "Reports")
        
        # Generate initial report
        self.generate_selected_report()
    
    def generate_selected_report(self):
        """Generate the currently selected report."""
        report_type = self.report_selector.currentText()
        
        if report_type == "Monthly Revenue Summary":
            self.generate_monthly_revenue_report()
        elif report_type == "Aging Analysis (30/60/90+ Days)":
            self.generate_aging_analysis_report()
        elif report_type == "Customer History":
            self.generate_customer_history_report()
        elif report_type == "Year-End Tax Summary":
            self.generate_tax_summary_report()
    
    def generate_monthly_revenue_report(self):
        """Generate monthly revenue summary by contract type."""
        from collections import defaultdict
        
        # Group payments by month and contract type
        monthly_data = defaultdict(lambda: {
            'storage': 0, 'tow': 0, 'recovery': 0, 'total': 0, 'count': 0
        })
        
        for contract in self.storage_data.contracts:
            contract_type = contract.contract_type.lower()
            
            # Add payments
            for payment in contract.payments:
                try:
                    payment_date = datetime.strptime(payment.date, "%Y-%m-%d")
                    month_key = payment_date.strftime("%Y-%m")
                    
                    monthly_data[month_key][contract_type] += payment.amount
                    monthly_data[month_key]['total'] += payment.amount
                    monthly_data[month_key]['count'] += 1
                except:
                    pass
        
        # Generate report
        report = "MONTHLY REVENUE SUMMARY\n"
        report += "=" * 80 + "\n"
        report += f"Generated: {datetime.today().strftime('%B %d, %Y')}\n"
        report += "=" * 80 + "\n\n"
        
        if not monthly_data:
            report += "No payment data available.\n"
        else:
            # Sort by month
            sorted_months = sorted(monthly_data.keys(), reverse=True)
            
            report += f"{'Month':<12} {'Storage':>12} {'Tow':>12} {'Recovery':>12} {'Total':>12} {'Payments':>10}\n"
            report += "-" * 80 + "\n"
            
            grand_total = 0
            total_payments = 0
            
            for month in sorted_months:
                data = monthly_data[month]
                month_display = datetime.strptime(month, "%Y-%m").strftime("%b %Y")
                
                report += f"{month_display:<12} "
                report += f"${data['storage']:>11,.2f} "
                report += f"${data['tow']:>11,.2f} "
                report += f"${data['recovery']:>11,.2f} "
                report += f"${data['total']:>11,.2f} "
                report += f"{data['count']:>10}\n"
                
                grand_total += data['total']
                total_payments += data['count']
            
            report += "-" * 80 + "\n"
            report += f"{'GRAND TOTAL':<12} {'':>12} {'':>12} {'':>12} "
            report += f"${grand_total:>11,.2f} {total_payments:>10}\n"
        
        self.report_display.setPlainText(report)
    
    def generate_aging_analysis_report(self):
        """Generate aging analysis for outstanding balances."""
        today = datetime.today()
        
        # Age buckets
        current = []  # 0-30 days
        days_30_60 = []  # 30-60 days
        days_60_90 = []  # 60-90 days
        over_90 = []  # 90+ days
        
        for contract in self.storage_data.contracts:
            bal = balance(contract)
            if bal <= 0:
                continue
            
            start_date = datetime.strptime(contract.start_date, "%Y-%m-%d")
            days_old = (today - start_date).days
            
            contract_info = {
                'id': contract.contract_id,
                'customer': contract.customer.name,
                'vehicle': f"{contract.vehicle.vehicle_type} {contract.vehicle.plate}",
                'balance': bal,
                'days': days_old,
                'type': contract.contract_type
            }
            
            if days_old <= 30:
                current.append(contract_info)
            elif days_old <= 60:
                days_30_60.append(contract_info)
            elif days_old <= 90:
                days_60_90.append(contract_info)
            else:
                over_90.append(contract_info)
        
        # Generate report
        report = "AGING ANALYSIS - OUTSTANDING BALANCES\n"
        report += "=" * 80 + "\n"
        report += f"As of: {today.strftime('%B %d, %Y')}\n"
        report += "=" * 80 + "\n\n"
        
        def format_bucket(bucket_name, contracts):
            section = f"\n{bucket_name}\n"
            section += "-" * 80 + "\n"
            
            if not contracts:
                section += "No contracts in this category.\n"
            else:
                section += f"{'ID':<6} {'Customer':<20} {'Vehicle':<20} {'Type':<10} {'Balance':>12}\n"
                section += "-" * 80 + "\n"
                
                total = 0
                for c in contracts:
                    section += f"{c['id']:<6} {c['customer'][:20]:<20} {c['vehicle'][:20]:<20} "
                    section += f"{c['type']:<10} ${c['balance']:>11,.2f}\n"
                    total += c['balance']
                
                section += "-" * 80 + "\n"
                section += f"Subtotal ({len(contracts)} contracts): ${total:,.2f}\n"
            
            return section
        
        report += format_bucket("CURRENT (0-30 Days)", current)
        report += format_bucket("30-60 DAYS", days_30_60)
        report += format_bucket("60-90 DAYS", days_60_90)
        report += format_bucket("OVER 90 DAYS", over_90)
        
        # Summary
        total_outstanding = sum(c['balance'] for bucket in [current, days_30_60, days_60_90, over_90] for c in bucket)
        total_count = sum(len(bucket) for bucket in [current, days_30_60, days_60_90, over_90])
        
        report += "\n" + "=" * 80 + "\n"
        report += f"TOTAL OUTSTANDING: ${total_outstanding:,.2f} across {total_count} contracts\n"
        report += "=" * 80 + "\n"
        
        self.report_display.setPlainText(report)
    
    def generate_customer_history_report(self):
        """Generate customer history report."""
        # Group contracts by customer
        from collections import defaultdict
        customer_data = defaultdict(list)
        
        for contract in self.storage_data.contracts:
            customer_data[contract.customer.name].append(contract)
        
        # Generate report
        report = "CUSTOMER HISTORY REPORT\n"
        report += "=" * 80 + "\n"
        report += f"Generated: {datetime.today().strftime('%B %d, %Y')}\n"
        report += f"Total Customers: {len(customer_data)}\n"
        report += "=" * 80 + "\n\n"
        
        for customer_name in sorted(customer_data.keys()):
            contracts = customer_data[customer_name]
            
            report += f"\nCUSTOMER: {customer_name}\n"
            report += "-" * 80 + "\n"
            
            total_charges = 0
            total_paid = 0
            
            for contract in contracts:
                bal = balance(contract)
                charges = balance(contract, include_breakdown=False)
                paid = sum(p.amount for p in contract.payments)
                
                report += f"  Contract #{contract.contract_id} - {contract.contract_type}\n"
                report += f"    Vehicle: {contract.vehicle.vehicle_type} {contract.vehicle.plate}\n"
                report += f"    Start Date: {contract.start_date}\n"
                report += f"    Total Charges: ${charges:,.2f}\n"
                report += f"    Payments: ${paid:,.2f} ({len(contract.payments)} payment(s))\n"
                report += f"    Balance: ${bal:,.2f}\n"
                report += f"    Status: {contract.status}\n\n"
                
                total_charges += charges
                total_paid += paid
            
            report += f"  CUSTOMER TOTALS:\n"
            report += f"    Contracts: {len(contracts)}\n"
            report += f"    Total Charges: ${total_charges:,.2f}\n"
            report += f"    Total Paid: ${total_paid:,.2f}\n"
            report += f"    Outstanding: ${total_charges - total_paid:,.2f}\n"
            report += "-" * 80 + "\n"
        
        self.report_display.setPlainText(report)
    
    def generate_tax_summary_report(self):
        """Generate year-end tax summary."""
        current_year = datetime.today().year
        
        # Calculate annual totals
        annual_revenue = 0
        contracts_started = 0
        total_payments = 0
        payment_count = 0
        
        revenue_by_type = {'storage': 0, 'tow': 0, 'recovery': 0}
        
        for contract in self.storage_data.contracts:
            # Count contracts started this year
            start_date = datetime.strptime(contract.start_date, "%Y-%m-%d")
            if start_date.year == current_year:
                contracts_started += 1
            
            # Sum payments made this year
            for payment in contract.payments:
                try:
                    payment_date = datetime.strptime(payment.date, "%Y-%m-%d")
                    if payment_date.year == current_year:
                        annual_revenue += payment.amount
                        total_payments += payment.amount
                        payment_count += 1
                        
                        contract_type = contract.contract_type.lower()
                        revenue_by_type[contract_type] += payment.amount
                except:
                    pass
        
        # Generate report
        report = f"YEAR-END TAX SUMMARY - {current_year}\n"
        report += "=" * 80 + "\n"
        report += f"Generated: {datetime.today().strftime('%B %d, %Y')}\n"
        report += "=" * 80 + "\n\n"
        
        report += "REVENUE SUMMARY\n"
        report += "-" * 80 + "\n"
        report += f"Total Revenue (Cash Basis):              ${annual_revenue:>15,.2f}\n"
        report += f"Number of Payments Received:              {payment_count:>15}\n"
        report += f"Average Payment Amount:                   ${annual_revenue/payment_count if payment_count > 0 else 0:>15,.2f}\n"
        report += "\n"
        
        report += "REVENUE BY CONTRACT TYPE\n"
        report += "-" * 80 + "\n"
        report += f"Storage Contracts:                        ${revenue_by_type['storage']:>15,.2f}\n"
        report += f"Tow Contracts:                            ${revenue_by_type['tow']:>15,.2f}\n"
        report += f"Recovery Contracts:                       ${revenue_by_type['recovery']:>15,.2f}\n"
        report += "-" * 80 + "\n"
        report += f"TOTAL REVENUE:                            ${annual_revenue:>15,.2f}\n"
        report += "\n"
        
        report += "BUSINESS ACTIVITY\n"
        report += "-" * 80 + "\n"
        report += f"New Contracts Started in {current_year}:        {contracts_started:>15}\n"
        report += f"Total Active Contracts:                   {len(self.storage_data.contracts):>15}\n"
        report += "\n"
        
        # Outstanding receivables
        outstanding = sum(balance(c) for c in self.storage_data.contracts if balance(c) > 0)
        report += "ACCOUNTS RECEIVABLE\n"
        report += "-" * 80 + "\n"
        report += f"Total Outstanding (Accrual Basis):        ${outstanding:>15,.2f}\n"
        report += "\n"
        
        report += "=" * 80 + "\n"
        report += "NOTE: This report is for informational purposes only.\n"
        report += "Please consult with a tax professional for accurate tax filing.\n"
        report += "=" * 80 + "\n"
        
        self.report_display.setPlainText(report)
    
    def export_current_report(self):
        """Export the currently displayed report to a text file."""
        report_type = self.report_selector.currentText()
        filename_base = report_type.lower().replace(' ', '_').replace('/', '_')
        timestamp = datetime.today().strftime('%Y%m%d')
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Report",
            f"{filename_base}_{timestamp}.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.report_display.toPlainText())
                QMessageBox.information(self, "Success", f"Report exported to:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export report:\n{str(e)}")
    
    def create_fee_tab(self):
        """Create the fee templates tab."""
        fee_widget = QScrollArea()
        fee_widget.setWidgetResizable(True)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        
        # Info label with licensing warning
        info_text = "Edit fee templates for each vehicle type. Changes are saved when you click 'Save Fee Templates'."
        if not ENABLE_INVOLUNTARY_TOWS:
            info_text += "\n\n⚠️ NOTICE: Recovery/involuntary towing features are disabled (no wrecker license). " \
                        "Only Storage and Tow (voluntary) fees are available. " \
                        "Admin fees are capped at $250 per Florida law."
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("padding: 10px; background-color: #fff3cd; border-radius: 5px;")
        layout.addWidget(info_label)
        
        self.fee_table = QTableWidget()
        
        # Build headers based on licensing mode
        headers = [
            "Vehicle Type",
            "Daily Storage",
            "Weekly Storage", 
            "Monthly Storage",
            "Tow Base",
            "Tow Mileage Rate",
            "Tow Labor Rate",
            "After Hours",
        ]
        
        # Only show recovery columns if involuntary towing enabled
        if ENABLE_INVOLUNTARY_TOWS:
            headers.extend([
                "Recovery Handling",
                "Lien Processing",
                "Cert Mail",
                "Title Search",
                "DMV Fee",
                "Sale Fee",
            ])
        
        headers.extend(["Admin Fee", "Labor Rate"])
        
        self.fee_table.setColumnCount(len(headers))
        self.fee_table.setHorizontalHeaderLabels(headers)
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
    
    def get_resize_edge(self, pos):
        """Determine which edge the mouse is near for resizing."""
        rect = self.rect()
        margin = self.resize_margin
        
        left = pos.x() < margin
        right = pos.x() > rect.width() - margin
        top = pos.y() < margin
        bottom = pos.y() > rect.height() - margin
        
        if top and left:
            return 'top_left'
        elif top and right:
            return 'top_right'
        elif bottom and left:
            return 'bottom_left'
        elif bottom and right:
            return 'bottom_right'
        elif top:
            return 'top'
        elif bottom:
            return 'bottom'
        elif left:
            return 'left'
        elif right:
            return 'right'
        return None
    
    def mousePressEvent(self, event):
        """Handle mouse press for resizing."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.resize_edge = self.get_resize_edge(event.pos())
            if self.resize_edge:
                self.resizing = True
                self.resize_start_pos = event.globalPosition().toPoint()
                self.resize_start_geometry = self.geometry()
                event.accept()
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for cursor changes and resizing."""
        if self.resizing and self.resize_edge:
            delta = event.globalPosition().toPoint() - self.resize_start_pos
            geo = self.resize_start_geometry
            
            x, y = geo.x(), geo.y()
            w, h = geo.width(), geo.height()
            
            if 'left' in self.resize_edge:
                x = geo.x() + delta.x()
                w = geo.width() - delta.x()
            if 'right' in self.resize_edge:
                w = geo.width() + delta.x()
            if 'top' in self.resize_edge:
                y = geo.y() + delta.y()
                h = geo.height() - delta.y()
            if 'bottom' in self.resize_edge:
                h = geo.height() + delta.y()
            
            # Apply minimum size constraints
            if w < self.minimumWidth():
                w = self.minimumWidth()
                if 'left' in self.resize_edge:
                    x = geo.x() + geo.width() - w
            if h < self.minimumHeight():
                h = self.minimumHeight()
                if 'top' in self.resize_edge:
                    y = geo.y() + geo.height() - h
            
            self.setGeometry(x, y, w, h)
            event.accept()
        else:
            # Update cursor based on edge
            edge = self.get_resize_edge(event.pos())
            if edge:
                if edge in ['top', 'bottom']:
                    self.setCursor(Qt.CursorShape.SizeVerCursor)
                elif edge in ['left', 'right']:
                    self.setCursor(Qt.CursorShape.SizeHorCursor)
                elif edge in ['top_left', 'bottom_right']:
                    self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                elif edge in ['top_right', 'bottom_left']:
                    self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release to end resizing."""
        if self.resizing:
            self.resizing = False
            self.resize_edge = None
            self.resize_start_pos = None
            self.resize_start_geometry = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def eventFilter(self, obj, event):
        """Event filter to handle resize from anywhere in the window."""
        from PyQt6.QtCore import QEvent
        
        # Only process events if this window is active
        if not self.isActiveWindow():
            # Clear any override cursor when window loses focus
            while QApplication.overrideCursor() is not None:
                QApplication.restoreOverrideCursor()
            self.current_cursor_edge = None
            return super().eventFilter(obj, event)
        
        # Only process mouse events
        if event.type() == QEvent.Type.MouseMove:
            # Get global position and convert to window coordinates
            global_pos = event.globalPosition().toPoint()
            window_pos = self.mapFromGlobal(global_pos)
            
            # Check if we're resizing
            if self.resizing:
                # Maintain appropriate cursor during resize - don't change it every frame
                pass
                
                # Continue resize operation
                delta = global_pos - self.resize_start_pos
                geo = self.resize_start_geometry
                
                x, y = geo.x(), geo.y()
                w, h = geo.width(), geo.height()
                
                if 'left' in self.resize_edge:
                    x = geo.x() + delta.x()
                    w = geo.width() - delta.x()
                if 'right' in self.resize_edge:
                    w = geo.width() + delta.x()
                if 'top' in self.resize_edge:
                    y = geo.y() + delta.y()
                    h = geo.height() - delta.y()
                if 'bottom' in self.resize_edge:
                    h = geo.height() + delta.y()
                
                # Apply minimum size constraints
                if w < self.minimumWidth():
                    w = self.minimumWidth()
                    if 'left' in self.resize_edge:
                        x = geo.x() + geo.width() - w
                if h < self.minimumHeight():
                    h = self.minimumHeight()
                    if 'top' in self.resize_edge:
                        y = geo.y() + geo.height() - h
                
                self.setGeometry(x, y, w, h)
                return True
            else:
                # Update cursor based on edge proximity (hover)
                edge = self.get_resize_edge(window_pos)
                
                # Only update cursor if edge changed
                if edge != self.current_cursor_edge:
                    # Clear any existing override cursor
                    while QApplication.overrideCursor() is not None:
                        QApplication.restoreOverrideCursor()
                    
                    # Set new cursor if on an edge
                    if edge:
                        if edge in ['top', 'bottom']:
                            QApplication.setOverrideCursor(Qt.CursorShape.SizeVerCursor)
                        elif edge in ['left', 'right']:
                            QApplication.setOverrideCursor(Qt.CursorShape.SizeHorCursor)
                        elif edge in ['top_left', 'bottom_right']:
                            QApplication.setOverrideCursor(Qt.CursorShape.SizeFDiagCursor)
                        elif edge in ['top_right', 'bottom_left']:
                            QApplication.setOverrideCursor(Qt.CursorShape.SizeBDiagCursor)
                    
                    self.current_cursor_edge = edge
        
        elif event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                # Get global position and convert to window coordinates
                global_pos = event.globalPosition().toPoint()
                window_pos = self.mapFromGlobal(global_pos)
                
                self.resize_edge = self.get_resize_edge(window_pos)
                if self.resize_edge:
                    self.resizing = True
                    self.resize_start_pos = global_pos
                    self.resize_start_geometry = self.geometry()
                    
                    # Override cursor is already set from hover, just keep it
                    return True
        
        elif event.type() == QEvent.Type.MouseButtonRelease:
            if self.resizing:
                self.resizing = False
                self.resize_edge = None
                self.resize_start_pos = None
                self.resize_start_geometry = None
                self.current_cursor_edge = None
                # Restore normal cursor
                while QApplication.overrideCursor() is not None:
                    QApplication.restoreOverrideCursor()
                return True
        
        return super().eventFilter(obj, event)
    
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
        
        # Calculate days in storage
        from datetime import datetime
        start_dt = datetime.strptime(contract.start_date, "%Y-%m-%d")
        today = datetime.today()
        days_stored = (today - start_dt).days
        
        # Determine next milestone for timeline display
        next_milestone = ""
        if contract.contract_type.lower() == "tow":
            if days_stored < 7:
                next_milestone = f"Payment due in {7 - days_stored}d"
            else:
                next_milestone = "Payment overdue"
        elif contract.contract_type.lower() == "recovery":
            lien_notice_date = timeline.get("lien_notice_deadline")
            sale_eligible_date = timeline.get("sale_eligible_date")
            if lien_notice_date:
                lien_dt = datetime.strptime(lien_notice_date, "%Y-%m-%d")
                days_to_lien = (lien_dt - today).days
                if days_to_lien > 0:
                    next_milestone = f"Lien notice: {days_to_lien}d"
                elif sale_eligible_date:
                    sale_dt = datetime.strptime(sale_eligible_date, "%Y-%m-%d")
                    days_to_sale = (sale_dt - today).days
                    if days_to_sale > 0:
                        next_milestone = f"Sale eligible: {days_to_sale}d"
                    else:
                        next_milestone = "SALE NOW"
        elif contract.contract_type.lower() == "storage":
            first_notice_date = timeline.get("first_notice_date")
            lien_eligible_date = timeline.get("lien_eligible_date")
            if first_notice_date and not past_due:
                notice_dt = datetime.strptime(first_notice_date, "%Y-%m-%d")
                days_to_notice = (notice_dt - today).days
                if days_to_notice > 0:
                    next_milestone = f"1st notice: {days_to_notice}d"
            elif lien_eligible_date:
                lien_dt = datetime.strptime(lien_eligible_date, "%Y-%m-%d")
                days_to_lien = (lien_dt - today).days
                if days_to_lien > 0:
                    next_milestone = f"Lien eligible: {days_to_lien}d"
                else:
                    next_milestone = "Lien ready"
        
        # Determine display status based on conditions
        if is_sale_eligible:
            display_status = "🔵 SALE ELIGIBLE"
        elif is_lien_eligible:
            display_status = f"🟠 {lien_status_text}"
        elif past_due:
            display_status = f"🔴 Past Due ({days_past_due}d)"
        else:
            display_status = f"✓ {contract.status}"
        
        # Add vehicle age for recovery contracts (affects timeline)
        if contract.contract_type.lower() == "recovery" and contract.vehicle.year:
            current_year = datetime.today().year
            vehicle_age = current_year - contract.vehicle.year
            vehicle += f" ({vehicle_age}yr)"
        
        # Create table items
        id_item = QTableWidgetItem(str(contract.contract_id))
        name_item = QTableWidgetItem(contract.customer.name)
        vehicle_item = QTableWidgetItem(vehicle)
        type_item = QTableWidgetItem(contract.contract_type)
        date_item = QTableWidgetItem(contract.start_date)
        balance_item = QTableWidgetItem(f"${bal:.2f}")
        days_item = QTableWidgetItem(str(days_stored))
        milestone_item = QTableWidgetItem(next_milestone)
        status_item = QTableWidgetItem(display_status)
        
        # Apply color coding based on status level
        if is_sale_eligible:
            # Blue background for sale eligible
            for item in [id_item, name_item, vehicle_item, type_item, date_item, balance_item, days_item, milestone_item, status_item]:
                item.setBackground(QColor("#e3f2fd"))  # Light blue
            status_item.setForeground(QColor("#1565c0"))  # Dark blue
        elif is_lien_eligible:
            # Orange background for lien eligible
            for item in [id_item, name_item, vehicle_item, type_item, date_item, balance_item, days_item, milestone_item, status_item]:
                item.setBackground(QColor("#fff3e0"))  # Light orange
            status_item.setForeground(QColor("#e65100"))  # Dark orange
        elif past_due:
            # Light red background for past due
            for item in [id_item, name_item, vehicle_item, type_item, date_item, balance_item, days_item, milestone_item, status_item]:
                item.setBackground(QColor("#ffebee"))  # Light red
            status_item.setForeground(QColor("#c62828"))  # Dark red
        
        # Bold milestone text if urgent (< 3 days)
        if "0d" in next_milestone or "1d" in next_milestone or "2d" in next_milestone:
            milestone_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            milestone_item.setForeground(QColor("#c62828"))
        
        # Set items in table
        self.contract_table.setItem(row_index, 0, id_item)
        self.contract_table.setItem(row_index, 1, name_item)
        self.contract_table.setItem(row_index, 2, vehicle_item)
        self.contract_table.setItem(row_index, 3, type_item)
        self.contract_table.setItem(row_index, 4, date_item)
        self.contract_table.setItem(row_index, 5, balance_item)
        self.contract_table.setItem(row_index, 6, days_item)
        self.contract_table.setItem(row_index, 7, milestone_item)
        self.contract_table.setItem(row_index, 8, status_item)
            
    def refresh_contracts(self):
        """Refresh the contract table only."""
        self.contract_table.setRowCount(len(self.storage_data.contracts))
        
        for i, contract in enumerate(self.storage_data.contracts):
            self.populate_contract_row(i, contract)
        
        # Update dashboard notification badge
        self.update_notification_badge()
            
    def on_contract_selected(self):
        """Handle contract selection."""
        selected_rows = self.contract_table.selectedIndexes()
        if not selected_rows:
            self.summary_text.clear()
            return
            
        row = selected_rows[0].row()
        contract = self.storage_data.contracts[row]
        
        # Get status information
        past_due, days_past_due = past_due_status(contract)
        is_lien_eligible, lien_status = lien_eligibility(contract)
        timeline = lien_timeline(contract)
        is_sale_eligible = timeline.get("is_sale_eligible", False)
        
        # Build prominent status badge at top
        status_header = "=" * 60 + "\n"
        if is_sale_eligible:
            status_header += "🔵 STATUS: SALE ELIGIBLE - READY FOR AUCTION/SALE\n"
        elif is_lien_eligible:
            status_header += f"🟠 STATUS: LIEN ELIGIBLE - {lien_status.upper()}\n"
        elif past_due:
            status_header += f"🔴 STATUS: PAST DUE - {days_past_due} DAYS OVERDUE\n"
        elif balance(contract) == 0:
            status_header += "✅ STATUS: PAID IN FULL\n"
        else:
            status_header += f"✅ STATUS: CURRENT - Balance ${balance(contract):.2f}\n"
        status_header += "=" * 60 + "\n\n"
        
        # Get basic contract summary
        summary = format_contract_summary(contract)
        
        # Build lien & sale timeline section
        timeline_section = "\n\n" + "="*60 + "\n"
        timeline_section += "LIEN & SALE TIMELINE\n"
        timeline_section += "="*60 + "\n\n"
        
        contract_type_lower = contract.contract_type.lower()
        
        # Display timeline based on contract type
        if contract_type_lower == "tow":
            # Tow contracts have no lien process
            timeline_section += "Voluntary tow contract - No lien process\n"
            timeline_section += "Payment expected within 7 days\n"
            if timeline.get('warnings'):
                timeline_section += "\n" + timeline['warnings'][0] + "\n"
        
        elif contract_type_lower == "recovery":
            # Recovery contracts use FL 713.78 timeline
            timeline_section += f"Vehicle Age:        {timeline.get('vehicle_age', 'N/A')} years\n"
            timeline_section += f"Lien Notice Due:    {timeline.get('lien_notice_deadline', 'N/A')}\n"
            if contract.first_notice_sent_date:
                timeline_section += f"Lien Notice Sent:   {contract.first_notice_sent_date}\n"
            else:
                timeline_section += "Lien Notice Sent:   NOT SENT\n"
            timeline_section += "\n"
            timeline_section += f"Sale Eligible Date: {timeline.get('sale_eligible_date', 'N/A')}\n"
            if timeline.get('is_sale_eligible'):
                timeline_section += "Sale Status:        ✓ SALE ELIGIBLE\n"
            else:
                days = timeline.get('days_until_sale', 0)
                timeline_section += f"Sale Status:        Not yet eligible ({days} days)\n"
        
        else:
            # Storage contracts have notice timeline
            timeline_section += f"First Notice Due:   {timeline.get('first_notice_date', 'N/A')}\n"
            if contract.first_notice_sent_date:
                timeline_section += f"First Notice Sent:  {contract.first_notice_sent_date}\n"
            else:
                timeline_section += "First Notice Sent:  NOT SENT\n"
            
            timeline_section += "\n"
            
            timeline_section += f"Second Notice Due:  {timeline.get('second_notice_date', 'N/A')}\n"
            if contract.second_notice_sent_date:
                timeline_section += f"Second Notice Sent: {contract.second_notice_sent_date}\n"
            else:
                timeline_section += "Second Notice Sent: NOT SENT\n"
            
            timeline_section += "\n"
            
            timeline_section += f"Lien Eligible Date: {timeline.get('lien_eligible_date', 'N/A')}\n"
            if is_lien_eligible:
                timeline_section += "Lien Status:        ✓ LIEN ELIGIBLE\n"
            else:
                timeline_section += f"Lien Status:        Not yet eligible ({lien_status})\n"
        
        timeline_section += "\n"
        
        # Sale eligibility information (contract type specific)
        sale_date = timeline.get('sale_eligible_date') or timeline.get('sale_earliest_date', 'N/A')
        is_sale_eligible = timeline.get('is_sale_eligible', False)
        
        if contract_type_lower == "recovery" and contract.vehicle.year:
            vehicle_age = datetime.today().year - contract.vehicle.year
            sale_wait = timeline.get('sale_wait_days', 35)
            timeline_section += f"Vehicle Age:        {vehicle_age} years ({contract.vehicle.year})\n"
            timeline_section += f"Sale Wait Period:   {sale_wait} days from recovery\n"
        
        if sale_date != 'N/A':
            timeline_section += f"Earliest Sale Date: {sale_date}\n"
            if is_sale_eligible:
                timeline_section += "Sale Status:        ✓ SALE ELIGIBLE\n"
            else:
                days = timeline.get('days_until_sale', 0)
                if days > 0:
                    timeline_section += f"Sale Status:        Not yet eligible ({days} days)\n"
                else:
                    timeline_section += "Sale Status:        Not eligible\n"
        
        # Warnings and alerts
        if timeline.get('warnings'):
            timeline_section += "\n" + "-"*60 + "\n"
            timeline_section += "ALERTS & WARNINGS:\n"
            timeline_section += "-"*60 + "\n"
            for warning in timeline['warnings']:
                timeline_section += f"{warning}\n"
        
        # Combine and display with status badge at top
        full_summary = status_header + summary + timeline_section
        self.summary_text.setText(full_summary)
        
    def filter_contracts(self, text):
        """Filter contracts based on search text (legacy - now uses apply_filters)."""
        self.apply_filters()
    
    def apply_filters(self):
        """Apply all active filters to the contract table."""
        filtered = list(self.storage_data.contracts)
        active_filters = []
        
        # Search text filter (multi-field)
        search_text = self.search_input.text().strip().lower()
        if search_text:
            filtered = [c for c in filtered 
                       if search_text in c.customer.name.lower() or
                          search_text in (c.customer.phone or "").lower() or
                          search_text in c.vehicle.vehicle_type.lower() or
                          search_text in c.vehicle.make.lower() or
                          search_text in c.vehicle.model.lower() or
                          search_text in c.vehicle.plate.lower() or
                          search_text in (c.vehicle.vin or "").lower() or
                          search_text in str(c.contract_id)]
            active_filters.append(f"Search: '{search_text}'")
        
        # Contract type filter
        type_filter = self.type_filter.currentText()
        if type_filter != "All Types":
            filtered = [c for c in filtered if c.contract_type.lower() == type_filter.lower()]
            active_filters.append(f"Type: {type_filter}")
        
        # Status filter
        status_filter = self.status_filter.currentText()
        if status_filter != "All Status":
            if status_filter == "Active":
                filtered = [c for c in filtered if c.status != "Paid" and balance(c) > 0]
            elif status_filter == "Paid":
                filtered = [c for c in filtered if c.status == "Paid" or balance(c) == 0]
            elif status_filter == "Past Due":
                filtered = [c for c in filtered if past_due_status(c)[0]]
            elif status_filter == "Lien Eligible":
                filtered = [c for c in filtered if lien_eligibility(c)[0]]
            elif status_filter == "Sale Eligible":
                filtered = [c for c in filtered if lien_timeline(c).get("is_sale_eligible", False)]
            active_filters.append(f"Status: {status_filter}")
        
        # Date range filter
        date_from = self.date_from.text().strip()
        date_to = self.date_to.text().strip()
        
        if date_from:
            try:
                from_date = datetime.strptime(date_from, "%Y-%m-%d")
                filtered = [c for c in filtered 
                           if datetime.strptime(c.start_date, "%Y-%m-%d") >= from_date]
                active_filters.append(f"From: {date_from}")
            except ValueError:
                pass  # Invalid date format, skip filter
        
        if date_to:
            try:
                to_date = datetime.strptime(date_to, "%Y-%m-%d")
                filtered = [c for c in filtered 
                           if datetime.strptime(c.start_date, "%Y-%m-%d") <= to_date]
                active_filters.append(f"To: {date_to}")
            except ValueError:
                pass  # Invalid date format, skip filter
        
        # Update filter count label
        if active_filters:
            self.filter_count_label.setText(f"✓ {len(active_filters)} filter(s) active | Showing {len(filtered)} of {len(self.storage_data.contracts)} contracts")
        else:
            self.filter_count_label.setText(f"Showing all {len(filtered)} contracts")
        
        # Update table
        self.contract_table.setRowCount(len(filtered))
        for i, contract in enumerate(filtered):
            self.populate_contract_row(i, contract)
    
    def clear_filters(self):
        """Clear all active filters."""
        self.search_input.clear()
        self.type_filter.setCurrentIndex(0)
        self.status_filter.setCurrentIndex(0)
        self.date_from.clear()
        self.date_to.clear()
        self.apply_filters()
    
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
    
    def record_payment(self):
        """Record a payment for selected contract."""
        selected_rows = self.contract_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a contract to record payment.")
            return
        
        row = selected_rows[0].row()
        contract = self.storage_data.contracts[row]
        current_balance = balance(contract)
        
        if current_balance <= 0:
            QMessageBox.information(self, "Paid in Full", "This contract has a zero balance.")
            return
        
        # Create payment dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Record Payment - Contract #{contract.contract_id}")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Show current info
        info_label = QLabel(f"Customer: {contract.customer.name}\\n"
                           f"Vehicle: {contract.vehicle.vehicle_type} {contract.vehicle.plate}\\n"
                           f"Current Balance: ${current_balance:.2f}")
        info_label.setStyleSheet("font-weight: bold; padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(info_label)
        
        # Payment amount
        form_layout = QFormLayout()
        amount_input = QLineEdit()
        amount_input.setPlaceholderText(f"${current_balance:.2f}")
        amount_input.setText(f"{current_balance:.2f}")
        form_layout.addRow("Payment Amount:", amount_input)
        
        # Payment method
        method_combo = QComboBox()
        method_combo.addItems(["Cash", "Check", "Credit Card", "Debit Card", "Money Order", "Wire Transfer"])
        form_layout.addRow("Payment Method:", method_combo)
        
        # Notes
        notes_input = QLineEdit()
        notes_input.setPlaceholderText("Optional notes")
        form_layout.addRow("Notes:", notes_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Record Payment")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        save_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                amount = float(amount_input.text())
                if amount <= 0:
                    QMessageBox.warning(self, "Invalid Amount", "Payment amount must be greater than zero.")
                    return
                
                # Record payment
                from lot_models import Payment
                payment = Payment(
                    date=datetime.today().strftime("%Y-%m-%d"),
                    amount=amount,
                    method=method_combo.currentText(),
                    note=notes_input.text()
                )
                contract.payments.append(payment)
                
                # Update status if paid in full
                new_balance = balance(contract)
                if new_balance <= 0:
                    contract.status = "Paid"
                
                # Save
                save_data(self.storage_data)
                self.refresh_contracts()
                
                # Show receipt
                receipt = f"PAYMENT RECEIPT\\n{'='*40}\\n"
                receipt += f"Date: {payment.date}\\n"
                receipt += f"Contract ID: {contract.contract_id}\\n"
                receipt += f"Customer: {contract.customer.name}\\n"
                receipt += f"Vehicle: {contract.vehicle.vehicle_type} {contract.vehicle.plate}\\n"
                receipt += f"\\nPayment Amount: ${payment.amount:.2f}\\n"
                receipt += f"Payment Method: {payment.method}\\n"
                receipt += f"Previous Balance: ${current_balance:.2f}\\n"
                receipt += f"New Balance: ${new_balance:.2f}\\n"
                if payment.note:
                    receipt += f"Notes: {payment.note}\\n"
                
                QMessageBox.information(self, "Payment Recorded", receipt)
                
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", "Please enter a valid payment amount.")
    
    def generate_lien_notice(self):
        """Generate official lien notice for selected contract."""
        selected_rows = self.contract_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a contract to generate lien notice.")
            return
        
        row = selected_rows[0].row()
        contract = self.storage_data.contracts[row]
        
        # Check if lien eligible
        is_eligible, status = lien_eligibility(contract)
        if not is_eligible:
            QMessageBox.warning(self, "Not Eligible", f"Contract not eligible for lien notice:\\n{status}")
            return
        
        # Generate notice
        timeline = lien_timeline(contract)
        current_balance = balance(contract)
        
        notice = "NOTICE OF LIEN AND SALE\\n"
        notice += "Florida Statute 713.78\\n"
        notice += "="*60 + "\\n\\n"
        notice += f"Date: {datetime.today().strftime('%B %d, %Y')}\\n\\n"
        notice += f"To: {contract.customer.name}\\n"
        if contract.customer.address:
            notice += f"    {contract.customer.address}\\n"
        if contract.customer.phone:
            notice += f"    Phone: {contract.customer.phone}\\n"
        notice += "\\n"
        notice += "VEHICLE INFORMATION:\\n"
        notice += f"  Year: {contract.vehicle.year or 'Unknown'}\\n"
        notice += f"  Make: {contract.vehicle.make}\\n"
        notice += f"  Model: {contract.vehicle.model}\\n"
        notice += f"  Color: {contract.vehicle.color}\\n"
        notice += f"  License Plate: {contract.vehicle.plate}\\n"
        notice += f"  VIN: {contract.vehicle.vin or 'Unknown'}\\n"
        notice += "\\n"
        notice += "NOTICE IS HEREBY GIVEN that the above-described vehicle has been\\n"
        notice += "in storage since " + contract.start_date + " and charges are due and unpaid.\\n"
        notice += "\\n"
        notice += f"TOTAL AMOUNT DUE: ${current_balance:.2f}\\n"
        notice += "\\n"
        notice += "IMPORTANT DATES:\\n"
        notice += f"  First Notice Due: {timeline.get('first_notice_due', 'N/A')}\\n"
        notice += f"  Lien Eligible: {timeline.get('lien_eligible_date', 'N/A')}\\n"
        notice += f"  Sale Eligible: {timeline.get('sale_eligible_date', 'N/A')}\\n"
        notice += "\\n"
        notice += "If payment is not received, the vehicle will be sold at public or\\n"
        notice += "private sale pursuant to Florida Statute 713.78.\\n"
        notice += "\\n"
        notice += "Contact immediately to make payment arrangements.\\n"
        
        # Show in dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Lien Notice")
        dialog.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(dialog)
        text_edit = QTextEdit()
        text_edit.setPlainText(notice)
        text_edit.setReadOnly(False)  # Allow editing before saving
        layout.addWidget(text_edit)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save to File")
        copy_btn = QPushButton("Copy to Clipboard")
        close_btn = QPushButton("Close")
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(copy_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        def save_notice():
            filename, _ = QFileDialog.getSaveFileName(dialog, "Save Lien Notice", 
                                                     f"lien_notice_{contract.contract_id}.txt",
                                                     "Text Files (*.txt)")
            if filename:
                with open(filename, 'w') as f:
                    f.write(text_edit.toPlainText())
                QMessageBox.information(dialog, "Saved", f"Lien notice saved to {filename}")
        
        def copy_notice():
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(text_edit.toPlainText())
            QMessageBox.information(dialog, "Copied", "Lien notice copied to clipboard")
        
        save_btn.clicked.connect(save_notice)
        copy_btn.clicked.connect(copy_notice)
        close_btn.clicked.connect(dialog.close)
        
        dialog.exec()
    
    def export_to_csv(self):
        """Export all contracts to CSV file."""
        if not self.storage_data.contracts:
            QMessageBox.information(self, "No Data", "No contracts to export.")
            return
        
        filename, _ = QFileDialog.getSaveFileName(self, "Export to CSV",
                                                  f"contracts_export_{datetime.today().strftime('%Y%m%d')}.csv",
                                                  "CSV Files (*.csv)")
        if not filename:
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow(['ID', 'Customer Name', 'Phone', 'Vehicle Type', 'Make', 'Model', 
                               'Year', 'Plate', 'VIN', 'Contract Type', 'Start Date', 'Rate Mode',
                               'Daily Fee', 'Weekly Fee', 'Monthly Fee', 'Balance', 'Status', 
                               'Days in Storage', 'Lien Eligible', 'Sale Eligible'])
                
                # Data rows
                for contract in self.storage_data.contracts:
                    bal = balance(contract)
                    is_lien_eligible, _ = lien_eligibility(contract)
                    timeline = lien_timeline(contract)
                    is_sale_eligible = timeline.get("is_sale_eligible", False)
                    
                    start_dt = datetime.strptime(contract.start_date, "%Y-%m-%d")
                    days_stored = (datetime.today() - start_dt).days
                    
                    writer.writerow([
                        contract.contract_id,
                        contract.customer.name,
                        contract.customer.phone,
                        contract.vehicle.vehicle_type,
                        contract.vehicle.make,
                        contract.vehicle.model,
                        contract.vehicle.year or '',
                        contract.vehicle.plate,
                        contract.vehicle.vin or '',
                        contract.contract_type,
                        contract.start_date,
                        contract.rate_mode,
                        contract.daily_storage_fee,
                        contract.weekly_storage_fee,
                        contract.monthly_storage_fee,
                        f"{bal:.2f}",
                        contract.status,
                        days_stored,
                        'Yes' if is_lien_eligible else 'No',
                        'Yes' if is_sale_eligible else 'No'
                    ])
            
            QMessageBox.information(self, "Success", f"Exported {len(self.storage_data.contracts)} contracts to {filename}")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
    
    def print_contract_summary(self):
        """Print detailed summary of selected contract."""
        selected_rows = self.contract_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a contract to print.")
            return
        
        row = selected_rows[0].row()
        contract = self.storage_data.contracts[row]
        
        # Get detailed summary
        summary = format_contract_summary(contract)
        timeline = lien_timeline(contract)
        
        # Build printable document
        doc = "STORAGE LOT CONTRACT SUMMARY\\n"
        doc += "="*70 + "\\n"
        doc += f"Printed: {datetime.today().strftime('%B %d, %Y at %I:%M %p')}\\n"
        doc += "="*70 + "\\n\\n"
        doc += summary
        doc += "\\n\\n" + "="*70 + "\\n"
        doc += "TIMELINE & STATUS\\n"
        doc += "="*70 + "\\n"
        doc += f"First Notice Due:  {timeline.get('first_notice_due', 'N/A')}\\n"
        doc += f"Lien Eligible:     {timeline.get('lien_eligible_date', 'N/A')}\\n"
        doc += f"Sale Eligible:     {timeline.get('sale_eligible_date', 'N/A')}\\n"
        
        # Show in dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Print Summary - Contract #{contract.contract_id}")
        dialog.setMinimumSize(700, 600)
        
        layout = QVBoxLayout(dialog)
        text_edit = QTextEdit()
        text_edit.setPlainText(doc)
        text_edit.setReadOnly(True)
        text_edit.setFontFamily("Courier New")
        layout.addWidget(text_edit)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save as PDF/Text")
        copy_btn = QPushButton("Copy to Clipboard")
        close_btn = QPushButton("Close")
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(copy_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        def save_doc():
            filename, _ = QFileDialog.getSaveFileName(dialog, "Save Summary",
                                                     f"contract_{contract.contract_id}_summary.txt",
                                                     "Text Files (*.txt)")
            if filename:
                with open(filename, 'w') as f:
                    f.write(text_edit.toPlainText())
                QMessageBox.information(dialog, "Saved", f"Summary saved to {filename}")
        
        def copy_doc():
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(text_edit.toPlainText())
            QMessageBox.information(dialog, "Copied", "Summary copied to clipboard")
        
        save_btn.clicked.connect(save_doc)
        copy_btn.clicked.connect(copy_doc)
        close_btn.clicked.connect(dialog.close)
        
        dialog.exec()
            
    def validate_admin_fee(self):
        """Validate admin fee doesn't exceed Florida cap."""
        try:
            fee = float(self.admin_fee.text() or 0)
            if fee > MAX_ADMIN_FEE:
                self.admin_fee_warning.setText(f"⚠ WARNING: Exceeds FL cap of ${MAX_ADMIN_FEE:.2f}")
                self.admin_fee.setStyleSheet("border: 2px solid #d32f2f;")
            else:
                self.admin_fee_warning.setText("")
                self.admin_fee.setStyleSheet("")
        except ValueError:
            self.admin_fee_warning.setText("")
            self.admin_fee.setStyleSheet("")
    
    def validate_lien_fee(self):
        """Validate lien processing fee doesn't exceed Florida cap."""
        try:
            fee = float(self.lien_processing_fee.text() or 0)
            admin_fee = float(self.admin_fee.text() or 0)
            total = fee + admin_fee
            
            if fee > MAX_LIEN_FEE:
                self.lien_fee_warning.setText(f"❌ CRITICAL: Lien fee exceeds ${MAX_LIEN_FEE:.2f} FL cap")
                self.lien_processing_fee.setStyleSheet("border: 2px solid #d32f2f;")
            elif total > MAX_LIEN_FEE:
                self.lien_fee_warning.setText(f"❌ CRITICAL: Admin+Lien (${total:.2f}) exceeds ${MAX_LIEN_FEE:.2f} cap")
                self.lien_processing_fee.setStyleSheet("border: 2px solid #d32f2f;")
            else:
                self.lien_fee_warning.setText("✓ Compliant")
                self.lien_fee_warning.setStyleSheet("color: #2e7d32; font-weight: bold;")
                self.lien_processing_fee.setStyleSheet("")
        except ValueError:
            self.lien_fee_warning.setText("")
            self.lien_processing_fee.setStyleSheet("")
    
    def validate_vin(self):
        """Validate VIN format (17 characters, alphanumeric, no I/O/Q)."""
        vin = self.vehicle_vin.text().upper()
        self.vehicle_vin.blockSignals(True)
        self.vehicle_vin.setText(vin)
        self.vehicle_vin.blockSignals(False)
        
        if not vin:
            self.vin_warning.setText("")
            self.vehicle_vin.setStyleSheet("")
            return
        
        # VIN validation rules
        invalid_chars = set('IOQ')
        has_invalid = any(c in invalid_chars for c in vin)
        is_alphanumeric = vin.replace(' ', '').isalnum()
        length = len(vin)
        
        if has_invalid:
            self.vin_warning.setText("⚠ VIN cannot contain I, O, or Q")
            self.vehicle_vin.setStyleSheet("border: 2px solid #ff9800;")
        elif not is_alphanumeric:
            self.vin_warning.setText("⚠ VIN must be alphanumeric only")
            self.vehicle_vin.setStyleSheet("border: 2px solid #ff9800;")
        elif length < 17:
            self.vin_warning.setText(f"⚠ VIN must be 17 characters ({length}/17)")
            self.vehicle_vin.setStyleSheet("border: 2px solid #ff9800;")
        else:
            self.vin_warning.setText("✓ Valid VIN")
            self.vin_warning.setStyleSheet("color: #2e7d32; font-size: 10px;")
            self.vehicle_vin.setStyleSheet("border: 2px solid #2e7d32;")
    
    def format_phone_number(self):
        """Auto-format phone number to (XXX) XXX-XXXX."""
        text = self.customer_phone.text()
        # Remove all non-digits
        digits = ''.join(filter(str.isdigit, text))
        
        # Limit to 10 digits
        if len(digits) > 10:
            digits = digits[:10]
        
        # Format based on length
        if len(digits) <= 3:
            formatted = digits
        elif len(digits) <= 6:
            formatted = f"({digits[:3]}) {digits[3:]}"
        elif len(digits) <= 10:
            formatted = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        else:
            formatted = digits
        
        # Update field without triggering textChanged again
        if formatted != text:
            self.customer_phone.blockSignals(True)
            self.customer_phone.setText(formatted)
            self.customer_phone.blockSignals(False)
        
        # Validate
        if digits and len(digits) < 10:
            self.phone_warning.setText(f"⚠ Phone must be 10 digits ({len(digits)}/10)")
            self.customer_phone.setStyleSheet("border: 2px solid #ff9800;")
        elif digits and len(digits) == 10:
            self.phone_warning.setText("✓ Valid phone")
            self.phone_warning.setStyleSheet("color: #2e7d32; font-size: 10px;")
            self.customer_phone.setStyleSheet("border: 2px solid #2e7d32;")
        else:
            self.phone_warning.setText("")
            self.customer_phone.setStyleSheet("")
    
    def format_license_plate(self):
        """Auto-uppercase license plate and validate."""
        text = self.vehicle_plate.text().upper()
        # Remove spaces and special characters except hyphens
        cleaned = ''.join(c for c in text if c.isalnum() or c == '-')
        
        if cleaned != self.vehicle_plate.text():
            self.vehicle_plate.blockSignals(True)
            self.vehicle_plate.setText(cleaned)
            self.vehicle_plate.blockSignals(False)
    
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
        
        # Trigger validation
        self.validate_admin_fee()
        if show_recovery:
            self.validate_lien_fee()
    
    def load_defaults_for_type(self):
        """Load default fees for selected vehicle type."""
        vtype = self.vehicle_type.currentText()
        if vtype not in self.fee_templates:
            return
            
        fees = self.fee_templates[vtype]
        
        # Common
        self.admin_fee.setText(str(fees.get("admin_fee", "0")))
        
        # Storage fees (all contracts)
        self.daily_storage_fee.setText(str(fees.get("daily_storage_fee", "0")))
        self.weekly_storage_fee.setText(str(fees.get("weekly_storage_fee", "0")))
        self.monthly_storage_fee.setText(str(fees.get("monthly_storage_fee", "0")))
        
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
        # Validate required fields
        errors = []
        
        if not self.customer_name.text().strip():
            errors.append("Customer Name is required")
        
        phone_digits = ''.join(filter(str.isdigit, self.customer_phone.text()))
        if not phone_digits:
            errors.append("Phone number is required")
        elif len(phone_digits) != 10:
            errors.append(f"Phone must be 10 digits (currently {len(phone_digits)})")
        
        if not self.vehicle_plate.text().strip():
            errors.append("License Plate is required")
        
        # Validate VIN if provided
        vin = self.vehicle_vin.text().strip()
        if vin:
            if len(vin) != 17:
                errors.append(f"VIN must be exactly 17 characters (currently {len(vin)})")
            elif not vin.isalnum():
                errors.append("VIN must be alphanumeric only")
            elif any(c in 'IOQ' for c in vin.upper()):
                errors.append("VIN cannot contain letters I, O, or Q")
        
        # Validate fees for recovery contracts
        if self.contract_type.currentText() == "Recovery":
            try:
                admin_fee = float(self.admin_fee.text() or 0)
                lien_fee = float(self.lien_processing_fee.text() or 0)
                if admin_fee + lien_fee > 250:
                    errors.append(f"Admin + Lien fees (${admin_fee + lien_fee:.2f}) exceed FL $250 cap")
            except ValueError:
                errors.append("Invalid fee values")
        
        # Show errors if any
        if errors:
            error_msg = "Please correct the following errors:\n\n" + "\n".join(f"• {err}" for err in errors)
            QMessageBox.warning(self, "Validation Error", error_msg)
            return
        
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
            
            # Get storage fees from form fields (user can override defaults)
            daily_storage_fee = float(self.daily_storage_fee.text() or 0)
            weekly_storage_fee = float(self.weekly_storage_fee.text() or 0)
            monthly_storage_fee = float(self.monthly_storage_fee.text() or 0)
            
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
            col = 0
            
            # Vehicle type (non-editable)
            vtype_item = QTableWidgetItem(vtype)
            vtype_item.setFlags(vtype_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.fee_table.setItem(i, col, vtype_item)
            col += 1
            
            # Storage fees (all contract types)
            self.fee_table.setItem(i, col, QTableWidgetItem(str(fees.get("daily_storage_fee", "0"))))
            col += 1
            self.fee_table.setItem(i, col, QTableWidgetItem(str(fees.get("weekly_storage_fee", "0"))))
            col += 1
            self.fee_table.setItem(i, col, QTableWidgetItem(str(fees.get("monthly_storage_fee", "0"))))
            col += 1
            
            # Tow fees (voluntary tow contracts)
            self.fee_table.setItem(i, col, QTableWidgetItem(str(fees.get("tow_base_fee", "0"))))
            col += 1
            self.fee_table.setItem(i, col, QTableWidgetItem(str(fees.get("tow_mileage_rate", "0"))))
            col += 1
            self.fee_table.setItem(i, col, QTableWidgetItem(str(fees.get("tow_hourly_labor_rate", "0"))))
            col += 1
            self.fee_table.setItem(i, col, QTableWidgetItem(str(fees.get("after_hours_fee", "0"))))
            col += 1
            
            # Recovery fees (only if involuntary towing enabled)
            if ENABLE_INVOLUNTARY_TOWS:
                self.fee_table.setItem(i, col, QTableWidgetItem(str(fees.get("recovery_handling_fee", "0"))))
                col += 1
                self.fee_table.setItem(i, col, QTableWidgetItem(str(fees.get("lien_processing_fee", "0"))))
                col += 1
                self.fee_table.setItem(i, col, QTableWidgetItem(str(fees.get("cert_mail_fee", "0"))))
                col += 1
                self.fee_table.setItem(i, col, QTableWidgetItem(str(fees.get("title_search_fee", "0"))))
                col += 1
                self.fee_table.setItem(i, col, QTableWidgetItem(str(fees.get("dmv_fee", "0"))))
                col += 1
                self.fee_table.setItem(i, col, QTableWidgetItem(str(fees.get("sale_fee", "0"))))
                col += 1
            
            # Common fees
            self.fee_table.setItem(i, col, QTableWidgetItem(str(fees.get("admin_fee", "0"))))
            col += 1
            self.fee_table.setItem(i, col, QTableWidgetItem(str(fees.get("labor_rate", "0"))))
            
    def save_fee_templates_action(self):
        """Save fee templates with validation."""
        try:
            for i in range(self.fee_table.rowCount()):
                vtype = self.fee_table.item(i, 0).text()
                if vtype in self.fee_templates:
                    col = 1
                    
                    # Storage fees
                    self.fee_templates[vtype]["daily_storage_fee"] = float(self.fee_table.item(i, col).text())
                    col += 1
                    self.fee_templates[vtype]["weekly_storage_fee"] = float(self.fee_table.item(i, col).text())
                    col += 1
                    self.fee_templates[vtype]["monthly_storage_fee"] = float(self.fee_table.item(i, col).text())
                    col += 1
                    
                    # Tow fees
                    self.fee_templates[vtype]["tow_base_fee"] = float(self.fee_table.item(i, col).text())
                    col += 1
                    self.fee_templates[vtype]["tow_mileage_rate"] = float(self.fee_table.item(i, col).text())
                    col += 1
                    self.fee_templates[vtype]["tow_hourly_labor_rate"] = float(self.fee_table.item(i, col).text())
                    col += 1
                    self.fee_templates[vtype]["after_hours_fee"] = float(self.fee_table.item(i, col).text())
                    col += 1
                    
                    # Recovery fees (only if enabled)
                    if ENABLE_INVOLUNTARY_TOWS:
                        self.fee_templates[vtype]["recovery_handling_fee"] = float(self.fee_table.item(i, col).text())
                        col += 1
                        self.fee_templates[vtype]["lien_processing_fee"] = float(self.fee_table.item(i, col).text())
                        col += 1
                        self.fee_templates[vtype]["cert_mail_fee"] = float(self.fee_table.item(i, col).text())
                        col += 1
                        self.fee_templates[vtype]["title_search_fee"] = float(self.fee_table.item(i, col).text())
                        col += 1
                        self.fee_templates[vtype]["dmv_fee"] = float(self.fee_table.item(i, col).text())
                        col += 1
                        self.fee_templates[vtype]["sale_fee"] = float(self.fee_table.item(i, col).text())
                        col += 1
                    
                    # Common fees with validation
                    admin_fee = float(self.fee_table.item(i, col).text())
                    if admin_fee > MAX_ADMIN_FEE:
                        raise ValueError(f"{vtype}: Admin fee ${admin_fee:.2f} exceeds FL cap of ${MAX_ADMIN_FEE:.2f}")
                    self.fee_templates[vtype]["admin_fee"] = admin_fee
                    col += 1
                    self.fee_templates[vtype]["labor_rate"] = float(self.fee_table.item(i, col).text())
                    
            save_fee_templates(self.fee_templates)
            QMessageBox.information(self, "Success", "Fee templates saved successfully!")
        except ValueError as ve:
            QMessageBox.critical(self, "Validation Error", f"Invalid fee value:\n{str(ve)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save fee templates: {str(e)}")
            
    def backup_data(self):
        """Create backup of current data with timestamp."""
        try:
            from persistence import backup_data as create_backup, DATA_PATH
            
            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = create_backup(DATA_PATH, f"_backup_{timestamp}")
            
            if backup_path:
                QMessageBox.information(self, "Backup Created", 
                                      f"Data backed up successfully to:\n{backup_path}")
            else:
                QMessageBox.warning(self, "Backup Failed", "Failed to create backup.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Backup failed: {str(e)}")
    
    def restore_data(self):
        """Restore data from backup file."""
        # Ask for confirmation
        reply = QMessageBox.question(self, "Restore from Backup",
                                    "This will replace your current data with the backup.\n"
                                    "Current data will be backed up first.\n\n"
                                    "Continue?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        # Select backup file
        filename, _ = QFileDialog.getOpenFileName(self, "Select Backup File",
                                                 str(Path.home() / "Desktop" / "storage lot program"),
                                                 "JSON Files (*.json)")
        if not filename:
            return
        
        try:
            from persistence import backup_data as create_backup, DATA_PATH, load_data
            
            # Backup current data first
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            create_backup(DATA_PATH, f"_before_restore_{timestamp}")
            
            # Copy backup file to data path
            import shutil
            shutil.copy(filename, DATA_PATH)
            
            # Reload data
            self.storage_data = load_data()
            self.refresh_contracts()
            
            QMessageBox.information(self, "Restore Complete",
                                  f"Data restored from:\n{filename}\n\n"
                                  f"Previous data backed up as:\n"
                                  f"lot_data_before_restore_{timestamp}.json")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Restore failed: {str(e)}")
    
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
        self.save_theme_preference()
    
    def manual_alert_check(self):
        """Manually check for urgent alerts and display them."""
        urgent_count = self.count_urgent_items()
        
        if urgent_count == 0:
            QMessageBox.information(self, "No Urgent Items", 
                                  "✓ Great! No urgent deadlines today.\n\n"
                                  "All contracts are current or have upcoming deadlines.")
        else:
            self.check_urgent_alerts()
    
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
        self.current_theme = theme_name
        colors = get_theme_colors(theme_name)
        
        # Update title bar
        self.title_bar.theme_colors = colors
        self.title_bar.setup_ui()
        
        # Apply stylesheet from theme_config
        stylesheet = get_application_stylesheet(colors)
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
