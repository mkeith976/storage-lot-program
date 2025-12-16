"""Dashboard components for the storage lot application."""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QFrame, QPushButton, QTableWidget, QTableWidgetItem)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt
from datetime import datetime
from utils.theme_config import (get_status_colors, get_stat_card_style, 
                          get_type_card_style, get_dashboard_widget_style)

if TYPE_CHECKING:
    from ui.theme_manager import ThemeManager


class DashboardCard(QFrame):
    """Base class for dashboard cards with theme support."""
    
    def __init__(self, theme_manager: 'ThemeManager', parent: Optional[QWidget] = None) -> None:
        """Initialize card.
        
        Args:
            theme_manager: ThemeManager instance for accessing current theme
            parent: Parent widget
        """
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setup_frame()
    
    def setup_frame(self):
        """Setup basic frame styling."""
        self.setFrameStyle(QFrame.Shape.Box)
    
    def get_colors(self):
        """Get current theme colors."""
        return self.theme_manager.get_colors()
    
    def get_status_colors(self):
        """Get status-specific colors based on current theme."""
        return get_status_colors(self.theme_manager.current_theme)


class StatCard(DashboardCard):
    """Statistic card showing a value with title and subtitle."""
    
    def __init__(self, theme_manager: 'ThemeManager', title: str, value: str, 
                 subtitle: str, color: str, parent: Optional[QWidget] = None) -> None:
        """Initialize stat card.
        
        Args:
            theme_manager: ThemeManager instance
            title: Card title
            value: Main value to display
            subtitle: Subtitle text
            color: Border and accent color
            parent: Parent widget
        """
        super().__init__(theme_manager, parent)
        self.title_text = title
        self.value_text = value
        self.subtitle_text = subtitle
        self.accent_color = color
        self.build_ui()
    
    def build_ui(self):
        """Build the card UI."""
        colors = self.get_colors()
        
        self.setLineWidth(2)
        self.setStyleSheet(get_stat_card_style(colors, self.accent_color))
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(self.title_text)
        title_label.setStyleSheet(f"color: {self.accent_color}; font-weight: bold; font-size: 11px;")
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(self.value_text)
        value_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {self.accent_color};")
        layout.addWidget(value_label)
        
        # Subtitle
        subtitle_label = QLabel(self.subtitle_text)
        subtitle_label.setStyleSheet(f"color: {colors['fg']}; font-size: 10px; opacity: 0.7;")
        layout.addWidget(subtitle_label)


class TypeCard(DashboardCard):
    """Contract type breakdown card."""
    
    def __init__(self, theme_manager: 'ThemeManager', title: str, count: int, 
                 revenue: float, color: str, parent: Optional[QWidget] = None) -> None:
        """Initialize type card.
        
        Args:
            theme_manager: ThemeManager instance
            title: Card title
            count: Contract count
            revenue: Revenue amount
            color: Border and accent color
            parent: Parent widget
        """
        super().__init__(theme_manager, parent)
        self.title_text = title
        self.count = count
        self.revenue = revenue
        self.accent_color = color
        self.build_ui()
    
    def build_ui(self):
        """Build the card UI."""
        colors = self.get_colors()
        
        self.setStyleSheet(get_type_card_style(colors, self.accent_color))
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(self.title_text)
        title_label.setStyleSheet(f"color: {self.accent_color}; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Count
        count_label = QLabel(f"Count: {self.count}")
        count_label.setStyleSheet(f"color: {colors['fg']};")
        layout.addWidget(count_label)
        
        # Revenue
        revenue_label = QLabel(f"Revenue: ${self.revenue:,.2f}")
        revenue_label.setStyleSheet(f"font-weight: bold; color: {colors['fg']};")
        layout.addWidget(revenue_label)


def create_dashboard_widget(theme_manager, storage_data, main_window):
    """Create the complete dashboard widget.
    
    Args:
        theme_manager: ThemeManager instance
        storage_data: Application data
        main_window: Main window for callbacks
        
    Returns:
        QWidget: Complete dashboard widget
    """
    from logic.lot_logic import balance, past_due_status, lien_eligibility, lien_timeline
    
    colors = theme_manager.get_colors()
    status_colors = get_status_colors(theme_manager.current_theme)
    
    dashboard_widget = QWidget()
    dashboard_widget.setObjectName("DashboardWidget")
    dashboard_widget.setStyleSheet(get_dashboard_widget_style(colors))
    layout = QVBoxLayout(dashboard_widget)
    layout.setSpacing(15)
    
    # Title
    title = QLabel("📊 Dashboard Overview")
    title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
    title.setStyleSheet(f"padding: 10px; color: {colors['accent']}; background-color: transparent;")
    layout.addWidget(title)
    
    # Calculate statistics
    total_contracts = len(storage_data.contracts)
    active_contracts = sum(1 for c in storage_data.contracts if c.status != "Paid")
    total_paid = sum(sum(p.amount for p in c.payments) for c in storage_data.contracts)
    outstanding = sum(balance(c, include_breakdown=False) for c in storage_data.contracts if balance(c) > 0)
    
    # Past due
    past_due_contracts = [c for c in storage_data.contracts if past_due_status(c)[0]]
    past_due_count = len(past_due_contracts)
    past_due_amount = sum(balance(c) for c in past_due_contracts)
    
    # Lien eligible
    lien_eligible_contracts = [c for c in storage_data.contracts if lien_eligibility(c)[0]]
    lien_eligible_count = len(lien_eligible_contracts)
    
    # Sale eligible
    sale_eligible_contracts = [c for c in storage_data.contracts 
                               if lien_timeline(c).get("is_sale_eligible", False)]
    sale_eligible_count = len(sale_eligible_contracts)
    
    # Stat cards row
    cards_layout = QHBoxLayout()
    
    card1 = StatCard(theme_manager, "Total Contracts", str(total_contracts),
                     f"{active_contracts} active", status_colors['primary'])
    cards_layout.addWidget(card1)
    
    card2 = StatCard(theme_manager, "Total Revenue", f"${total_paid:,.2f}",
                     f"${outstanding:,.2f} outstanding", status_colors['success'])
    cards_layout.addWidget(card2)
    
    color3 = status_colors['danger'] if past_due_count > 0 else status_colors['neutral']
    card3 = StatCard(theme_manager, "Past Due", str(past_due_count),
                     f"${past_due_amount:,.2f}" if past_due_count > 0 else "All current", color3)
    cards_layout.addWidget(card3)
    
    color4 = status_colors['warning'] if lien_eligible_count > 0 else status_colors['neutral']
    card4 = StatCard(theme_manager, "Lien Eligible", str(lien_eligible_count),
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
    storage_count = sum(1 for c in storage_data.contracts if c.contract_type.lower() == "storage")
    storage_revenue = sum(balance(c, include_breakdown=False) for c in storage_data.contracts 
                        if c.contract_type.lower() == "storage")
    storage_card = TypeCard(theme_manager, "Storage Contracts", storage_count,
                           storage_revenue, status_colors['primary'])
    breakdown_layout.addWidget(storage_card)
    
    # Tow
    tow_count = sum(1 for c in storage_data.contracts if c.contract_type.lower() == "tow")
    tow_revenue = sum(balance(c, include_breakdown=False) for c in storage_data.contracts 
                     if c.contract_type.lower() == "tow")
    tow_card = TypeCard(theme_manager, "Tow Contracts", tow_count,
                       tow_revenue, status_colors['success'])
    breakdown_layout.addWidget(tow_card)
    
    # Recovery
    recovery_count = sum(1 for c in storage_data.contracts if c.contract_type.lower() == "recovery")
    recovery_revenue = sum(balance(c, include_breakdown=False) for c in storage_data.contracts 
                          if c.contract_type.lower() == "recovery")
    recovery_card = TypeCard(theme_manager, "Recovery Contracts", recovery_count,
                            recovery_revenue, status_colors['danger'])
    breakdown_layout.addWidget(recovery_card)
    
    layout.addLayout(breakdown_layout)
    
    # Upcoming deadlines section
    deadline_label = QLabel("⚠️ Upcoming Deadlines (Next 7 Days)")
    deadline_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
    deadline_label.setStyleSheet(f"padding-top: 10px; color: {status_colors['danger']};")
    layout.addWidget(deadline_label)
    
    # Find upcoming deadlines
    upcoming = []
    today = datetime.today()
    
    for contract in storage_data.contracts:
        if balance(contract) > 0:
            timeline = lien_timeline(contract)
            for key, date_str in timeline.items():
                if isinstance(date_str, str) and key.endswith('_date'):
                    try:
                        deadline_date = datetime.strptime(date_str, "%Y-%m-%d")
                        days_until = (deadline_date - today).days
                        if 0 <= days_until <= 7:
                            upcoming.append({
                                'contract_id': contract.contract_id,
                                'customer': contract.customer.name,
                                'vehicle': f"{contract.vehicle.vehicle_type} {contract.vehicle.plate}",
                                'deadline': key.replace('_date', '').replace('_', ' ').title(),
                                'days': days_until
                            })
                    except:
                        pass
    
    if upcoming:
        upcoming.sort(key=lambda x: x['days'])
        
        deadline_table = QTableWidget()
        deadline_table.setColumnCount(5)
        deadline_table.setHorizontalHeaderLabels(['ID', 'Customer', 'Vehicle', 'Deadline Type', 'Days'])
        deadline_table.setRowCount(min(len(upcoming), 10))
        deadline_table.setMaximumHeight(250)
        
        for i, item in enumerate(upcoming[:10]):
            deadline_table.setItem(i, 0, QTableWidgetItem(str(item['contract_id'])))
            deadline_table.setItem(i, 1, QTableWidgetItem(item['customer']))
            deadline_table.setItem(i, 2, QTableWidgetItem(item['vehicle']))
            deadline_table.setItem(i, 3, QTableWidgetItem(item['deadline']))
            
            days_item = QTableWidgetItem(f"{item['days']} days" if item['days'] > 0 else "TODAY!")
            if item['days'] == 0:
                days_item.setForeground(QColor(status_colors['danger']))
                days_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            deadline_table.setItem(i, 4, days_item)
        
        deadline_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(deadline_table)
    else:
        no_deadlines = QLabel("✓ No urgent deadlines in the next 7 days")
        no_deadlines.setStyleSheet(f"color: {status_colors['success']}; padding: 10px; font-style: italic;")
        layout.addWidget(no_deadlines)
    
    # Quick actions
    actions_label = QLabel("Quick Actions")
    actions_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
    actions_label.setStyleSheet("padding-top: 10px;")
    layout.addWidget(actions_label)
    
    actions_layout = QHBoxLayout()
    
    new_contract_btn = QPushButton("➕ New Contract")
    new_contract_btn.clicked.connect(lambda: main_window.tabs.setCurrentIndex(2))
    new_contract_btn.setMinimumHeight(40)
    actions_layout.addWidget(new_contract_btn)
    
    export_btn = QPushButton("📊 Export Data")
    export_btn.clicked.connect(main_window.export_to_csv)
    export_btn.setMinimumHeight(40)
    actions_layout.addWidget(export_btn)
    
    backup_btn = QPushButton("💾 Backup Data")
    backup_btn.clicked.connect(main_window.backup_data)
    backup_btn.setMinimumHeight(40)
    actions_layout.addWidget(backup_btn)
    
    refresh_btn = QPushButton("🔄 Refresh Dashboard")
    refresh_btn.clicked.connect(main_window.refresh_dashboard)
    refresh_btn.setMinimumHeight(40)
    actions_layout.addWidget(refresh_btn)
    
    layout.addLayout(actions_layout)
    layout.addStretch()
    
    return dashboard_widget
