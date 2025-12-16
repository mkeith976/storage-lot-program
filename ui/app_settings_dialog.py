"""Application settings dialog for theme and preferences."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QWidget, QComboBox, QGroupBox, QFormLayout, QCheckBox,
    QSpinBox, QLineEdit, QFileDialog, QTabWidget, QScrollArea,
    QSizeGrip
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from utils.theme_config import get_theme_colors
from utils.settings_manager import SettingsManager


class AppSettingsDialog(QDialog):
    """Dialog for managing application settings."""
    
    def __init__(self, parent=None, current_theme='Dark', settings_manager=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_theme = current_theme
        self.settings_manager = settings_manager or SettingsManager()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the settings dialog UI."""
        self.setWindowTitle("Application Settings")
        self.setModal(True)
        self.resize(700, 550)
        
        # Remove default window frame to use themed styling
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        
        # Apply theme colors to dialog background
        colors = get_theme_colors(self.current_theme)
        self.setStyleSheet(f"QDialog {{ background-color: {colors['bg']}; color: {colors['fg']}; border: 1px solid {colors['border']}; }}")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Add custom title bar
        title_bar = QWidget()
        title_bar.setFixedHeight(35)
        title_bar.setStyleSheet(f"background-color: {colors['titlebar_bg']}; color: {colors['titlebar_fg']};")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 5, 0)
        
        title_label = QLabel("⚙️ Settings")
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
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
        
        # Store title bar for dragging
        self.title_bar = title_bar
        self.drag_position = None
        
        layout.addWidget(title_bar)
        
        # Add resize grip
        self.size_grip = QSizeGrip(self)
        self.size_grip.setFixedSize(20, 20)
        
        # Main content area with tabs
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)
        
        # Create tab widget for organized settings
        self.tabs = QTabWidget()
        
        # Create each settings tab
        self.tabs.addTab(self.create_appearance_tab(), "Appearance")
        self.tabs.addTab(self.create_display_tab(), "Display")
        self.tabs.addTab(self.create_behavior_tab(), "Behavior")
        self.tabs.addTab(self.create_alerts_tab(), "Alerts")
        self.tabs.addTab(self.create_backup_tab(), "Backup")
        self.tabs.addTab(self.create_defaults_tab(), "Defaults")
        self.tabs.addTab(self.create_business_tab(), "Business Info")
        self.tabs.addTab(self.create_reports_tab(), "Reports")
        
        content_layout.addWidget(self.tabs)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_to_defaults)
        btn_layout.addWidget(reset_btn)
        
        btn_layout.addStretch()
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(apply_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.save_and_close)
        ok_btn.setDefault(True)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        content_layout.addLayout(btn_layout)
        
        layout.addWidget(content_widget)
        
        # Load current settings
        self.load_current_settings()
    
    def create_appearance_tab(self):
        """Create appearance settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(15)
        
        # Theme/Color Scheme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            "Dark", "Light", "Blue Dark", "Green Dark", 
            "Purple Dark", "Warm Light", "Cool Light"
        ])
        layout.addRow("Color Scheme:", self.theme_combo)
        
        return widget
    
    def create_display_tab(self):
        """Create display settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(15)
        
        # Font Size
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItems(["Small", "Medium", "Large"])
        layout.addRow("Font Size:", self.font_size_combo)
        
        # Date Format
        self.date_format_combo = QComboBox()
        self.date_format_combo.addItems(["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"])
        layout.addRow("Date Format:", self.date_format_combo)
        
        # Time Format
        self.time_format_combo = QComboBox()
        self.time_format_combo.addItems(["12-hour", "24-hour"])
        layout.addRow("Time Format:", self.time_format_combo)
        
        # Compact Mode
        self.compact_mode_check = QCheckBox("Reduce spacing for more data on screen")
        layout.addRow("Compact Mode:", self.compact_mode_check)
        
        layout.addRow(QLabel(""))  # Spacer
        layout.addRow(QLabel("<i>Note: Font size and compact mode require restart</i>"))
        
        return widget
    
    def create_behavior_tab(self):
        """Create application behavior settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(15)
        
        # Auto-save Interval
        self.auto_save_spin = QSpinBox()
        self.auto_save_spin.setRange(1, 60)
        self.auto_save_spin.setSuffix(" minutes")
        layout.addRow("Auto-save Interval:", self.auto_save_spin)
        
        # Confirm Before Delete
        self.confirm_delete_check = QCheckBox("Ask for confirmation before deleting contracts")
        layout.addRow("Confirm Delete:", self.confirm_delete_check)
        
        # Show Tooltips
        self.show_tooltips_check = QCheckBox("Display helpful hints and tooltips")
        layout.addRow("Show Tooltips:", self.show_tooltips_check)
        
        # Startup Tab
        self.startup_tab_combo = QComboBox()
        self.startup_tab_combo.addItems([
            "Dashboard", "Intake", "Contracts", "Yard View"
        ])
        layout.addRow("Startup Tab:", self.startup_tab_combo)
        
        return widget
    
    def create_alerts_tab(self):
        """Create notifications and alerts settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(15)
        
        # Auto-check Alerts Frequency
        self.auto_check_spin = QSpinBox()
        self.auto_check_spin.setRange(0, 120)
        self.auto_check_spin.setSuffix(" minutes")
        self.auto_check_spin.setSpecialValueText("Manual only")
        layout.addRow("Auto-check Frequency:", self.auto_check_spin)
        
        # Desktop Notifications
        self.desktop_notif_check = QCheckBox("Show desktop notifications for urgent alerts")
        layout.addRow("Desktop Notifications:", self.desktop_notif_check)
        
        # Alert Sound
        self.alert_sound_check = QCheckBox("Play sound when alerts are found")
        layout.addRow("Alert Sound:", self.alert_sound_check)
        
        layout.addRow(QLabel(""))  # Spacer
        layout.addRow(QLabel("<i>Set auto-check to 0 for manual alerts only</i>"))
        
        return widget
    
    def create_backup_tab(self):
        """Create data and backup settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(15)
        
        # Auto-backup Frequency
        self.auto_backup_combo = QComboBox()
        self.auto_backup_combo.addItems(["Never", "Daily", "Weekly"])
        layout.addRow("Auto-backup:", self.auto_backup_combo)
        
        # Backup Location
        backup_layout = QHBoxLayout()
        self.backup_location_edit = QLineEdit()
        backup_layout.addWidget(self.backup_location_edit)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_backup_location)
        backup_layout.addWidget(browse_btn)
        layout.addRow("Backup Location:", backup_layout)
        
        # Keep Records For
        self.keep_records_spin = QSpinBox()
        self.keep_records_spin.setRange(0, 3650)
        self.keep_records_spin.setSuffix(" days")
        self.keep_records_spin.setSpecialValueText("Forever")
        layout.addRow("Keep Records For:", self.keep_records_spin)
        
        layout.addRow(QLabel(""))  # Spacer
        layout.addRow(QLabel("<i>Set keep records to 0 to keep all records forever</i>"))
        
        return widget
    
    def create_defaults_tab(self):
        """Create default values settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(15)
        
        # Default Vehicle Type
        self.default_vehicle_combo = QComboBox()
        self.default_vehicle_combo.addItems([
            "Car", "Truck", "Motorcycle", "RV", "Boat", "Trailer"
        ])
        layout.addRow("Default Vehicle Type:", self.default_vehicle_combo)
        
        # Default Payment Method
        self.default_payment_combo = QComboBox()
        self.default_payment_combo.addItems([
            "Cash", "Check", "Card", "Money Order", "Wire Transfer"
        ])
        layout.addRow("Default Payment Method:", self.default_payment_combo)
        
        # Default Admin Fee
        self.default_admin_edit = QLineEdit()
        self.default_admin_edit.setPlaceholderText("Leave empty to use fee template")
        layout.addRow("Default Admin Fee:", self.default_admin_edit)
        
        layout.addRow(QLabel(""))  # Spacer
        layout.addRow(QLabel("<i>These values pre-fill forms to speed up data entry</i>"))
        
        return widget
    
    def create_business_tab(self):
        """Create business information settings tab."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(15)
        
        # Business Name
        self.business_name_edit = QLineEdit()
        self.business_name_edit.setPlaceholderText("Your Business Name")
        layout.addRow("Business Name:", self.business_name_edit)
        
        # Business Address
        self.business_address_edit = QLineEdit()
        self.business_address_edit.setPlaceholderText("123 Main St, City, State ZIP")
        layout.addRow("Address:", self.business_address_edit)
        
        # Business Phone
        self.business_phone_edit = QLineEdit()
        self.business_phone_edit.setPlaceholderText("(555) 123-4567")
        layout.addRow("Phone:", self.business_phone_edit)
        
        # Business Email
        self.business_email_edit = QLineEdit()
        self.business_email_edit.setPlaceholderText("info@yourbusiness.com")
        layout.addRow("Email:", self.business_email_edit)
        
        # Business Logo
        logo_layout = QHBoxLayout()
        self.business_logo_edit = QLineEdit()
        self.business_logo_edit.setPlaceholderText("No logo selected")
        logo_layout.addWidget(self.business_logo_edit)
        logo_browse_btn = QPushButton("Browse...")
        logo_browse_btn.clicked.connect(self.browse_logo)
        logo_layout.addWidget(logo_browse_btn)
        layout.addRow("Logo:", logo_layout)
        
        layout.addRow(QLabel(""))  # Spacer
        layout.addRow(QLabel("<i>Business info appears on forms, reports, and lien notices</i>"))
        
        scroll.setWidget(widget)
        return scroll
    
    def create_reports_tab(self):
        """Create reports settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(15)
        
        # Include Photos
        self.include_photos_check = QCheckBox("Include vehicle photos in generated reports")
        layout.addRow("Photos in Reports:", self.include_photos_check)
        
        # Report Footer
        self.report_footer_edit = QLineEdit()
        self.report_footer_edit.setPlaceholderText("Optional footer text")
        layout.addRow("Report Footer:", self.report_footer_edit)
        
        layout.addRow(QLabel(""))  # Spacer
        layout.addRow(QLabel("<i>Customize how reports and exports are generated</i>"))
        
        return widget
    
    def load_current_settings(self):
        """Load current settings into UI controls."""
        # Appearance
        self.theme_combo.setCurrentText(self.settings_manager.get('theme', 'Dark'))
        
        # Display
        self.font_size_combo.setCurrentText(self.settings_manager.get('font_size', 'Medium'))
        self.date_format_combo.setCurrentText(self.settings_manager.get('date_format', 'MM/DD/YYYY'))
        self.time_format_combo.setCurrentText(self.settings_manager.get('time_format', '12-hour'))
        self.compact_mode_check.setChecked(self.settings_manager.get('compact_mode', False))
        
        # Behavior
        self.auto_save_spin.setValue(self.settings_manager.get('auto_save_interval', 5))
        self.confirm_delete_check.setChecked(self.settings_manager.get('confirm_before_delete', True))
        self.show_tooltips_check.setChecked(self.settings_manager.get('show_tooltips', True))
        self.startup_tab_combo.setCurrentText(self.settings_manager.get('startup_tab', 'Dashboard'))
        
        # Alerts
        self.auto_check_spin.setValue(self.settings_manager.get('auto_check_alerts', 30))
        self.desktop_notif_check.setChecked(self.settings_manager.get('desktop_notifications', False))
        self.alert_sound_check.setChecked(self.settings_manager.get('alert_sound', False))
        
        # Backup
        self.auto_backup_combo.setCurrentText(self.settings_manager.get('auto_backup', 'Daily'))
        self.backup_location_edit.setText(self.settings_manager.get('backup_location', ''))
        self.keep_records_spin.setValue(self.settings_manager.get('keep_records_days', 365))
        
        # Defaults
        self.default_vehicle_combo.setCurrentText(self.settings_manager.get('default_vehicle_type', 'Car'))
        self.default_payment_combo.setCurrentText(self.settings_manager.get('default_payment_method', 'Cash'))
        self.default_admin_edit.setText(self.settings_manager.get('default_admin_fee', ''))
        
        # Business Info
        self.business_name_edit.setText(self.settings_manager.get('business_name', ''))
        self.business_address_edit.setText(self.settings_manager.get('business_address', ''))
        self.business_phone_edit.setText(self.settings_manager.get('business_phone', ''))
        self.business_email_edit.setText(self.settings_manager.get('business_email', ''))
        self.business_logo_edit.setText(self.settings_manager.get('business_logo_path', ''))
        
        # Reports
        self.include_photos_check.setChecked(self.settings_manager.get('include_photos_in_reports', True))
        self.report_footer_edit.setText(self.settings_manager.get('report_footer_text', ''))
    
    def save_current_settings(self):
        """Save UI controls to settings."""
        # Appearance
        self.settings_manager.set('theme', self.theme_combo.currentText())
        
        # Display
        self.settings_manager.set('font_size', self.font_size_combo.currentText())
        self.settings_manager.set('date_format', self.date_format_combo.currentText())
        self.settings_manager.set('time_format', self.time_format_combo.currentText())
        self.settings_manager.set('compact_mode', self.compact_mode_check.isChecked())
        
        # Behavior
        self.settings_manager.set('auto_save_interval', self.auto_save_spin.value())
        self.settings_manager.set('confirm_before_delete', self.confirm_delete_check.isChecked())
        self.settings_manager.set('show_tooltips', self.show_tooltips_check.isChecked())
        self.settings_manager.set('startup_tab', self.startup_tab_combo.currentText())
        
        # Alerts
        self.settings_manager.set('auto_check_alerts', self.auto_check_spin.value())
        self.settings_manager.set('desktop_notifications', self.desktop_notif_check.isChecked())
        self.settings_manager.set('alert_sound', self.alert_sound_check.isChecked())
        
        # Backup
        self.settings_manager.set('auto_backup', self.auto_backup_combo.currentText())
        self.settings_manager.set('backup_location', self.backup_location_edit.text())
        self.settings_manager.set('keep_records_days', self.keep_records_spin.value())
        
        # Defaults
        self.settings_manager.set('default_vehicle_type', self.default_vehicle_combo.currentText())
        self.settings_manager.set('default_payment_method', self.default_payment_combo.currentText())
        self.settings_manager.set('default_admin_fee', self.default_admin_edit.text())
        
        # Business Info
        self.settings_manager.set('business_name', self.business_name_edit.text())
        self.settings_manager.set('business_address', self.business_address_edit.text())
        self.settings_manager.set('business_phone', self.business_phone_edit.text())
        self.settings_manager.set('business_email', self.business_email_edit.text())
        self.settings_manager.set('business_logo_path', self.business_logo_edit.text())
        
        # Reports
        self.settings_manager.set('include_photos_in_reports', self.include_photos_check.isChecked())
        self.settings_manager.set('report_footer_text', self.report_footer_edit.text())
        
        # Save to file
        self.settings_manager.save_settings()
    
    def browse_backup_location(self):
        """Browse for backup location folder."""
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Select Backup Location",
            self.backup_location_edit.text()
        )
        if folder:
            self.backup_location_edit.setText(folder)
    
    def browse_logo(self):
        """Browse for business logo file."""
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Select Business Logo",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file:
            self.business_logo_edit.setText(file)
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.settings_manager.reset_to_defaults()
            self.load_current_settings()
    
    def apply_settings(self):
        """Apply settings without closing."""
        self.save_current_settings()
        
        selected_theme = self.theme_combo.currentText()
        if hasattr(self.parent_window, 'theme_manager'):
            self.parent_window.theme_manager.apply_theme(selected_theme)
            # Update dialog colors
            colors = get_theme_colors(selected_theme)
            self.setStyleSheet(f"QDialog {{ background-color: {colors['bg']}; color: {colors['fg']}; border: 1px solid {colors['border']}; }}")
            self.title_bar.setStyleSheet(f"background-color: {colors['titlebar_bg']}; color: {colors['titlebar_fg']};")
            self.current_theme = selected_theme
    
    def save_and_close(self):
        """Save settings and close dialog."""
        self.save_current_settings()
        self.apply_settings()
        self.accept()
    
    def mousePressEvent(self, event):
        """Handle mouse press for window dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
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
    
    def resizeEvent(self, event):
        """Handle window resize to reposition size grip."""
        super().resizeEvent(event)
        # Position size grip in bottom-right corner
        self.size_grip.move(
            self.width() - self.size_grip.width(),
            self.height() - self.size_grip.height()
        )
