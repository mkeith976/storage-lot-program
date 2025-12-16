"""Custom table delegate that applies theme colors to table items."""
from PyQt6.QtWidgets import QStyledItemDelegate, QStyle
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtCore import Qt
from utils.theme_config import get_theme_colors


class ThemedTableDelegate(QStyledItemDelegate):
    """Delegate that applies theme colors to table cells."""
    
    def __init__(self, parent=None, theme='Dark'):
        super().__init__(parent)
        self.theme = theme
        self.update_colors()
    
    def update_colors(self):
        """Update colors from theme configuration."""
        colors = get_theme_colors(self.theme)
        self.bg_color = QColor(colors['input_bg'])
        self.fg_color = QColor(colors['input_fg'])
        self.selected_bg_color = QColor(colors['button_bg'])
        self.selected_fg_color = QColor(colors['button_fg'])
    
    def set_theme(self, theme):
        """Change the theme and update colors."""
        self.theme = theme
        self.update_colors()
    
    def initStyleOption(self, option, index):
        """Initialize style options with theme colors."""
        super().initStyleOption(option, index)
        
        # Set background and text colors based on selection state
        if option.state & QStyle.StateFlag.State_Selected:
            option.palette.setColor(QPalette.ColorRole.Base, self.selected_bg_color)
            option.palette.setColor(QPalette.ColorRole.Text, self.selected_fg_color)
            option.palette.setColor(QPalette.ColorRole.Highlight, self.selected_bg_color)
            option.palette.setColor(QPalette.ColorRole.HighlightedText, self.selected_fg_color)
        else:
            option.palette.setColor(QPalette.ColorRole.Base, self.bg_color)
            option.palette.setColor(QPalette.ColorRole.Text, self.fg_color)
        
        option.backgroundBrush = option.palette.brush(QPalette.ColorRole.Base)
