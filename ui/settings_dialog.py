"""Settings dialog for fee templates and application configuration."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QFont

from utils.config import ENABLE_INVOLUNTARY_TOWS
from utils.persistence import save_fee_templates
from utils.theme_config import get_theme_colors


class SettingsDialog(QDialog):
    """Dialog for managing application settings including fee templates."""
    
    def __init__(self, parent=None, fee_templates=None, current_theme='Dark'):
        super().__init__(parent)
        self.fee_templates = fee_templates or {}
        self.current_theme = current_theme
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the settings dialog UI."""
        self.setWindowTitle("Fee Templates")
        self.setModal(True)
        self.resize(1000, 600)
        
        # Remove default window frame to use themed styling
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        
        # Apply theme colors to dialog background
        colors = get_theme_colors(self.current_theme)
        self.setStyleSheet(f"QDialog {{ background-color: {colors['bg']}; color: {colors['fg']}; border: 1px solid {colors['border']}; }}")
        
        layout = QVBoxLayout(self)
        
        # Add custom title bar
        title_bar = QWidget()
        title_bar.setFixedHeight(35)
        title_bar.setStyleSheet(f"background-color: {colors['titlebar_bg']}; color: {colors['titlebar_fg']};")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 5, 0)
        
        title_label = QLabel("⚙️ Fees")
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Store title bar for dragging
        self.title_bar = title_bar
        self.drag_position = None
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(35, 30)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['titlebar_bg']};
                color: {colors['titlebar_fg']};
                border: none;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #e81123;
                color: white;
            }}
        """)
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)
        
        # Add resize grip for bottom-right corner
        from PyQt6.QtWidgets import QSizeGrip
        self.size_grip = QSizeGrip(self)
        self.size_grip.setStyleSheet(f"background-color: {colors['bg']};")
        
        # Position size grip in bottom-right corner
        grip_size = 16
        self.size_grip.setFixedSize(grip_size, grip_size)
        
        layout.addWidget(title_bar)
        
        # Main content layout
        content_layout = QVBoxLayout()
        
        # Info label with licensing warning
        info_text = "Edit fee templates for each vehicle type. Changes are saved when you click 'Save & Close'."
        if not ENABLE_INVOLUNTARY_TOWS:
            info_text += "\n\n⚠️ NOTICE: Recovery/involuntary towing features are disabled (no wrecker license). " \
                        "Only Storage and Tow (voluntary) fees are available. " \
                        "Admin fees are capped at $250 per Florida law."
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        colors = get_theme_colors(self.current_theme)
        info_label.setStyleSheet(f"padding: 10px; background-color: {colors['frame_bg']}; color: {colors['fg']}; border: 1px solid {colors['border']}; border-radius: 5px;")
        content_layout.addWidget(info_label)
        
        # Fee table
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
        for i in range(len(headers)):
            self.fee_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        content_layout.addWidget(self.fee_table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save & Close")
        save_btn.clicked.connect(self.save_and_close)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        btn_layout.addStretch()
        content_layout.addLayout(btn_layout)
        
        layout.addLayout(content_layout)
        
        # Load data
        self.refresh_fee_table()
    
    def resizeEvent(self, event):
        """Position size grip in bottom-right corner on resize."""
        super().resizeEvent(event)
        if hasattr(self, 'size_grip'):
            grip_size = 16
            self.size_grip.move(self.width() - grip_size, self.height() - grip_size)
    
    def refresh_fee_table(self):
        """Refresh the fee templates table.
        Note: QTableWidgetItem doesn't inherit CSS, so we apply colors programmatically
        but read them from the theme configuration to keep styling centralized.
        """
        # Get colors from theme config (centralized styling)
        colors = get_theme_colors(self.current_theme)
        bg_color = QBrush(QColor(colors['input_bg']))
        fg_color = QBrush(QColor(colors['input_fg']))
        
        self.fee_table.setRowCount(len(self.fee_templates))
        
        for i, (vtype, fees) in enumerate(self.fee_templates.items()):
            col = 0
            
            # Vehicle type (non-editable)
            vtype_item = QTableWidgetItem(vtype)
            vtype_item.setFlags(vtype_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            vtype_item.setBackground(bg_color)
            vtype_item.setForeground(fg_color)
            self.fee_table.setItem(i, col, vtype_item)
            col += 1
            
            # Helper to create and style items
            def create_item(value):
                item = QTableWidgetItem(str(value))
                item.setBackground(bg_color)
                item.setForeground(fg_color)
                return item
            
            # Storage fees (all contract types)
            self.fee_table.setItem(i, col, create_item(fees.get("daily_storage_fee", "0")))
            col += 1
            self.fee_table.setItem(i, col, create_item(fees.get("weekly_storage_fee", "0")))
            col += 1
            self.fee_table.setItem(i, col, create_item(fees.get("monthly_storage_fee", "0")))
            col += 1
            
            # Tow fees (voluntary tow contracts)
            self.fee_table.setItem(i, col, create_item(fees.get("tow_base_fee", "0")))
            col += 1
            self.fee_table.setItem(i, col, create_item(fees.get("tow_mileage_rate", "0")))
            col += 1
            self.fee_table.setItem(i, col, create_item(fees.get("tow_hourly_labor_rate", "0")))
            col += 1
            self.fee_table.setItem(i, col, create_item(fees.get("after_hours_fee", "0")))
            col += 1
            
            # Recovery fees (only if involuntary towing enabled)
            if ENABLE_INVOLUNTARY_TOWS:
                self.fee_table.setItem(i, col, create_item(fees.get("recovery_handling_fee", "0")))
                col += 1
                self.fee_table.setItem(i, col, create_item(fees.get("lien_processing_fee", "0")))
                col += 1
                self.fee_table.setItem(i, col, create_item(fees.get("cert_mail_fee", "0")))
                col += 1
                self.fee_table.setItem(i, col, create_item(fees.get("title_search_fee", "0")))
                col += 1
                self.fee_table.setItem(i, col, create_item(fees.get("dmv_fee", "0")))
                col += 1
                self.fee_table.setItem(i, col, create_item(fees.get("sale_fee", "0")))
                col += 1
            
            # Common fees
            self.fee_table.setItem(i, col, create_item(fees.get("admin_fee", "0")))
            col += 1
            self.fee_table.setItem(i, col, create_item(fees.get("labor_rate", "0")))
    
    def save_and_close(self):
        """Save fee templates with validation."""
        try:
            for i in range(self.fee_table.rowCount()):
                vtype = self.fee_table.item(i, 0).text()
                col = 1
                
                if vtype in self.fee_templates:
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
                    
                    # Common fees
                    self.fee_templates[vtype]["admin_fee"] = float(self.fee_table.item(i, col).text())
                    col += 1
                    self.fee_templates[vtype]["labor_rate"] = float(self.fee_table.item(i, col).text())
            
            # Save to file
            save_fee_templates(self.fee_templates)
            QMessageBox.information(self, "Success", "Fee templates saved successfully!")
            self.accept()
            
        except ValueError as e:
            QMessageBox.critical(self, "Invalid Input", f"Please enter valid numbers for all fees.\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save fee templates:\n{str(e)}")
    
    def mousePressEvent(self, event):
        """Handle mouse press for window dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if click is on title bar
            if hasattr(self, 'title_bar') and self.title_bar.geometry().contains(event.pos()):
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for window dragging."""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release to stop dragging."""
        self.drag_position = None
