"""Centralized theme management for the application."""
from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING
from utils.theme_config import get_theme_colors, get_application_stylesheet

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QMainWindow


class ThemeManager:
    """Manages application theming and theme switching."""
    
    def __init__(self, main_window: 'QMainWindow') -> None:
        """Initialize theme manager.
        
        Args:
            main_window: The main application window
        """
        self.main_window = main_window
        self.current_theme = "Dark"
        self.load_preference()
        
    def load_preference(self):
        """Load saved theme preference from file."""
        try:
            theme_file = Path(__file__).parent.parent / "data" / "theme_preference.txt"
            if theme_file.exists():
                saved = theme_file.read_text().strip()
                if saved in ["Dark", "Light"]:
                    self.current_theme = saved
        except Exception:
            pass
    
    def save_preference(self):
        """Save current theme preference to file."""
        try:
            theme_file = Path(__file__).parent.parent / "data" / "theme_preference.txt"
            theme_file.write_text(self.current_theme)
        except Exception:
            pass
    
    def apply_theme(self, theme_name: str):
        """Apply a theme to the entire application.
        
        Args:
            theme_name: Name of theme ('Dark' or 'Light')
        """
        from PyQt6.QtWidgets import QApplication
        
        self.current_theme = theme_name
        colors = get_theme_colors(theme_name)
        
        # Get stylesheet
        stylesheet = get_application_stylesheet(colors)
        
        # Apply to entire application (not just main window)
        QApplication.instance().setStyleSheet(stylesheet)
        
        # Also apply to main window for good measure
        self.main_window.setStyleSheet(stylesheet)
        
        # Update title bar
        if hasattr(self.main_window, 'title_bar'):
            self.main_window.title_bar.theme_colors = colors
            self.main_window.title_bar.setup_ui()
        
        # Force widget updates
        self._force_widget_refresh()
        
        # Refresh dashboard if it exists
        if hasattr(self.main_window, 'refresh_dashboard'):
            self.main_window.refresh_dashboard()
        
        # Save preference
        self.save_preference()
    
    def toggle_theme(self):
        """Toggle between Dark and Light themes."""
        new_theme = "Light" if self.current_theme == "Dark" else "Dark"
        self.apply_theme(new_theme)
    
    def _force_widget_refresh(self):
        """Force all widgets to refresh their styling."""
        # Force repaint
        self.main_window.update()
        
        if hasattr(self.main_window, 'tabs'):
            self.main_window.tabs.update()
        
        if hasattr(self.main_window, 'status_label'):
            self.main_window.status_label.update()
    
    def get_colors(self):
        """Get current theme colors dictionary."""
        return get_theme_colors(self.current_theme)
