"""Application settings manager with persistent storage."""
import json
from pathlib import Path
from typing import Dict, Any, Optional


class SettingsManager:
    """Manages application settings with JSON persistence."""
    
    def __init__(self, settings_path: Optional[Path] = None):
        """Initialize settings manager.
        
        Args:
            settings_path: Path to settings file. Defaults to data/app_settings.json
        """
        if settings_path is None:
            base_dir = Path(__file__).resolve().parent.parent
            data_dir = base_dir / "data"
            data_dir.mkdir(exist_ok=True)
            self.settings_path = data_dir / "app_settings.json"
        else:
            self.settings_path = settings_path
        
        self.settings = self._load_settings()
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Get default settings."""
        return {
            # Appearance
            "theme": "Dark",
            
            # Display
            "font_size": "Medium",
            "date_format": "MM/DD/YYYY",
            "time_format": "12-hour",
            "compact_mode": False,
            
            # Application Behavior
            "auto_save_interval": 5,  # minutes
            "confirm_before_delete": True,
            "show_tooltips": True,
            "startup_tab": "Dashboard",
            
            # Notifications & Alerts
            "auto_check_alerts": 30,  # minutes (0 = manual only)
            "desktop_notifications": False,
            "alert_sound": False,
            
            # Data & Backup
            "auto_backup": "Daily",
            "backup_location": str(Path.home() / "Documents" / "LotBackups"),
            "keep_records_days": 365,  # 0 = forever
            
            # Default Values
            "default_vehicle_type": "Car",
            "default_payment_method": "Cash",
            "default_admin_fee": "",  # Empty = use fee template
            
            # Business Info
            "business_name": "",
            "business_address": "",
            "business_phone": "",
            "business_email": "",
            "business_logo_path": "",
            
            # Reports
            "include_photos_in_reports": True,
            "report_footer_text": "",
        }
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file or return defaults."""
        if not self.settings_path.exists():
            return self._get_defaults()
        
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            
            # Merge with defaults to ensure new settings are present
            defaults = self._get_defaults()
            defaults.update(loaded)
            return defaults
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self._get_defaults()
    
    def save_settings(self) -> bool:
        """Save current settings to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure data directory exists
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value.
        
        Args:
            key: Setting key
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a setting value.
        
        Args:
            key: Setting key
            value: Setting value
        """
        self.settings[key] = value
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        self.settings = self._get_defaults()
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings.
        
        Returns:
            Dictionary of all settings
        """
        return self.settings.copy()
