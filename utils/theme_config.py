"""Theme and styling configuration for the application."""

def get_theme_colors(theme_name):
    """Return color scheme for the given theme."""
    if theme_name == "Dark":
        return {
            "bg": "#2b2b2b",
            "fg": "#ffffff",
            "frame_bg": "#3c3c3c",
            "frame_fg": "#ffffff",
            "input_bg": "#505050",
            "input_fg": "#ffffff",
            "button_bg": "#0d47a1",
            "button_fg": "#ffffff",
            "button_hover": "#1565c0",
            "header_bg": "#1e1e1e",
            "titlebar_bg": "#1e1e1e",
            "titlebar_fg": "#ffffff",
            "entry_bg": "#454545",
            "entry_fg": "#ffffff",
            "select_bg": "#0078d4",
            "select_fg": "#ffffff",
            "tree_odd": "#2b2b2b",
            "tree_even": "#333333",
            "accent": "#42a5f5",
            "border": "#42a5f5",
        }
    elif theme_name == "Light":
        return {
            "bg": "#f5f5f5",
            "fg": "#000000",
            "frame_bg": "#ffffff",
            "frame_fg": "#000000",
            "input_bg": "#ffffff",
            "input_fg": "#000000",
            "button_bg": "#1976d2",
            "button_fg": "#ffffff",
            "button_hover": "#2196f3",
            "header_bg": "#e0e0e0",
            "titlebar_bg": "#e0e0e0",
            "titlebar_fg": "#000000",
            "entry_bg": "#ffffff",
            "entry_fg": "#000000",
            "select_bg": "#0078d4",
            "select_fg": "#ffffff",
            "tree_odd": "#ffffff",
            "tree_even": "#f0f0f0",
            "accent": "#1976d2",
            "border": "#1976d2",
        }
    elif theme_name == "Blue Dark":
        return {
            "bg": "#1a2332",
            "fg": "#e0e6ed",
            "frame_bg": "#233043",
            "frame_fg": "#e0e6ed",
            "input_bg": "#2d3e52",
            "input_fg": "#e0e6ed",
            "button_bg": "#1565c0",
            "button_fg": "#ffffff",
            "button_hover": "#1976d2",
            "header_bg": "#0f1821",
            "titlebar_bg": "#0f1821",
            "titlebar_fg": "#e0e6ed",
            "entry_bg": "#2d3e52",
            "entry_fg": "#e0e6ed",
            "select_bg": "#1976d2",
            "select_fg": "#ffffff",
            "tree_odd": "#1a2332",
            "tree_even": "#233043",
            "accent": "#42a5f5",
            "border": "#42a5f5",
        }
    elif theme_name == "Green Dark":
        return {
            "bg": "#1e2a1e",
            "fg": "#e0ede0",
            "frame_bg": "#2a3b2a",
            "frame_fg": "#e0ede0",
            "input_bg": "#364836",
            "input_fg": "#e0ede0",
            "button_bg": "#2e7d32",
            "button_fg": "#ffffff",
            "button_hover": "#388e3c",
            "header_bg": "#141a14",
            "titlebar_bg": "#141a14",
            "titlebar_fg": "#e0ede0",
            "entry_bg": "#364836",
            "entry_fg": "#e0ede0",
            "select_bg": "#43a047",
            "select_fg": "#ffffff",
            "tree_odd": "#1e2a1e",
            "tree_even": "#2a3b2a",
            "accent": "#66bb6a",
            "border": "#66bb6a",
        }
    elif theme_name == "Purple Dark":
        return {
            "bg": "#2a1e2e",
            "fg": "#ede0f0",
            "frame_bg": "#3b2a40",
            "frame_fg": "#ede0f0",
            "input_bg": "#483650",
            "input_fg": "#ede0f0",
            "button_bg": "#6a1b9a",
            "button_fg": "#ffffff",
            "button_hover": "#7b1fa2",
            "header_bg": "#1a141e",
            "titlebar_bg": "#1a141e",
            "titlebar_fg": "#ede0f0",
            "entry_bg": "#483650",
            "entry_fg": "#ede0f0",
            "select_bg": "#8e24aa",
            "select_fg": "#ffffff",
            "tree_odd": "#2a1e2e",
            "tree_even": "#3b2a40",
            "accent": "#ba68c8",
            "border": "#ba68c8",
        }
    elif theme_name == "Warm Light":
        return {
            "bg": "#faf8f5",
            "fg": "#2e2520",
            "frame_bg": "#fff9f0",
            "frame_fg": "#2e2520",
            "input_bg": "#ffffff",
            "input_fg": "#2e2520",
            "button_bg": "#d84315",
            "button_fg": "#ffffff",
            "button_hover": "#e64a19",
            "header_bg": "#f5ebe0",
            "titlebar_bg": "#f5ebe0",
            "titlebar_fg": "#2e2520",
            "entry_bg": "#ffffff",
            "entry_fg": "#2e2520",
            "select_bg": "#ff6f00",
            "select_fg": "#ffffff",
            "tree_odd": "#faf8f5",
            "tree_even": "#f5ebe0",
            "accent": "#ff6f00",
            "border": "#ff6f00",
        }
    elif theme_name == "Cool Light":
        return {
            "bg": "#f0f4f8",
            "fg": "#1a2530",
            "frame_bg": "#f8fbff",
            "frame_fg": "#1a2530",
            "input_bg": "#ffffff",
            "input_fg": "#1a2530",
            "button_bg": "#0288d1",
            "button_fg": "#ffffff",
            "button_hover": "#039be5",
            "header_bg": "#e0e8f0",
            "titlebar_bg": "#e0e8f0",
            "titlebar_fg": "#1a2530",
            "entry_bg": "#ffffff",
            "entry_fg": "#1a2530",
            "select_bg": "#0288d1",
            "select_fg": "#ffffff",
            "tree_odd": "#f0f4f8",
            "tree_even": "#e0e8f0",
            "accent": "#039be5",
            "border": "#039be5",
        }
    else:  # Default to Dark
        return get_theme_colors("Dark")


def get_application_stylesheet(colors):
    """Return the main application stylesheet."""
    return f"""
        QMainWindow {{
            background-color: {colors['bg']};
            color: {colors['fg']};
            border: none;
        }}
        QWidget {{
            color: {colors['fg']};
        }}
        QDialog {{
            background-color: {colors['frame_bg']};
            color: {colors['fg']};
        }}
        QScrollArea {{
            border: none;
            background-color: transparent;
        }}
        QScrollArea > QWidget > QWidget {{
            background-color: {colors['frame_bg']};
        }}
        QTabWidget {{
            border: 0px solid transparent;
            background: {colors['titlebar_bg']};
        }}
        QTabWidget::pane {{
            border: 0px solid transparent;
            border-top: 0px solid transparent;
            background: {colors['frame_bg']};
            margin: 0px;
            padding: 0px;
            top: 0px;
        }}
        QTabBar {{
            border: 0px solid transparent;
            background: {colors['titlebar_bg']};
            margin: 0px;
            padding: 0px;
        }}
        QTabBar::tab {{
            background: {colors['frame_bg']};
            color: {colors['fg']};
            padding: 10px 20px;
            margin: 0px;
            margin-bottom: 0px;
            border: 0px solid transparent;
        }}
        QTabBar::tab:selected {{
            background: {colors['bg']};
            font-weight: bold;
            border: 0px solid transparent;
        }}
        QTabBar::tab:hover {{
            background: {colors['header_bg']};
        }}
        QLabel {{
            color: {colors['fg']};
            background: transparent;
        }}
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit {{
            background-color: {colors['input_bg']};
            color: {colors['input_fg']};
            border: 2px solid {colors['accent']};
            border-radius: 4px;
            padding: 5px;
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {{
            border: 2px solid {colors['button_hover']};
            background-color: {colors['entry_bg']};
        }}
        QComboBox {{
            background-color: {colors['input_bg']};
            color: {colors['input_fg']};
            border: 2px solid {colors['accent']};
            border-radius: 4px;
            padding: 5px;
            padding-right: 25px;
        }}
        QComboBox:focus {{
            border: 2px solid {colors['button_hover']};
            background-color: {colors['entry_bg']};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left: 1px solid {colors['border']};
            background: {colors['input_bg']};
            border-top-right-radius: 3px;
            border-bottom-right-radius: 3px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {colors['fg']};
            margin-right: 3px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {colors['input_bg']};
            color: {colors['input_fg']};
            border: 2px solid {colors['accent']};
            selection-background-color: {colors['select_bg']};
            selection-color: {colors['select_fg']};
        }}
        QPushButton {{
            background-color: {colors['button_bg']};
            color: {colors['button_fg']};
            border: none;
            border-radius: 3px;
            padding: 8px 15px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {colors['button_hover']};
        }}
        QPushButton:pressed {{
            background-color: #0a3a8a;
        }}
        QPushButton:disabled {{
            background-color: #555;
            color: #888;
        }}
        QTableWidget {{
            background-color: {colors['frame_bg']};
            color: {colors['fg']};
            gridline-color: {colors['border']};
            border: 1px solid {colors['border']};
            selection-background-color: {colors['button_bg']};
            selection-color: {colors['button_fg']};
        }}
        QTableWidget::item {{
            padding: 5px;
            background-color: {colors['input_bg']};
            color: {colors['input_fg']};
        }}
        QTableWidget::item:selected {{
            background-color: {colors['button_bg']};
            color: {colors['button_fg']};
        }}
        QTableView {{
            background-color: {colors['frame_bg']};
            color: {colors['fg']};
        }}
        QHeaderView::section {{
            background-color: {colors['header_bg']};
            color: {colors['fg']};
            padding: 8px;
            border: none;
            font-weight: bold;
        }}
        QScrollBar:vertical {{
            background: {colors['frame_bg']};
            width: 12px;
            border: none;
        }}
        QScrollBar::handle:vertical {{
            background: #555;
            border-radius: 6px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: #777;
        }}
        QScrollBar:horizontal {{
            background: {colors['frame_bg']};
            height: 12px;
            border: none;
        }}
        QScrollBar::handle:horizontal {{
            background: #555;
            border-radius: 6px;
            min-width: 20px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: #777;
        }}
        QFrame {{
            background-color: {colors['frame_bg']};
            color: {colors['fg']};
        }}
        QCheckBox {{
            color: {colors['fg']};
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid #555;
            border-radius: 3px;
            background: {colors['input_bg']};
        }}
        QCheckBox::indicator:checked {{
            background: {colors['button_bg']};
            border-color: {colors['button_bg']};
        }}
        QRadioButton {{
            color: {colors['fg']};
            spacing: 8px;
        }}
        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid #555;
            border-radius: 9px;
            background: {colors['input_bg']};
        }}
        QRadioButton::indicator:checked {{
            background: {colors['button_bg']};
            border-color: {colors['button_bg']};
        }}
        QGroupBox {{
            color: {colors['fg']};
            border: 1px solid #555;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            font-weight: bold;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 5px;
        }}
        QMenuBar {{
            background-color: {colors['titlebar_bg']};
            color: {colors['titlebar_fg']};
            border: none;
        }}
        QMenuBar::item:selected {{
            background-color: {colors['button_bg']};
        }}
        QMenu {{
            background-color: {colors['frame_bg']};
            color: {colors['fg']};
            border: 1px solid #555;
        }}
        QMenu::item:selected {{
            background-color: {colors['button_bg']};
        }}
        QStatusBar {{
            background-color: {colors['titlebar_bg']};
            color: {colors['titlebar_fg']};
            border: none;
        }}
    """


def get_status_colors(theme_name):
    """Return status-specific colors based on theme.
    
    Args:
        theme_name: 'Dark' or 'Light'
        
    Returns:
        dict: Status colors (primary, success, danger, warning, neutral)
    """
    colors = get_theme_colors(theme_name)
    
    return {
        'primary': colors['accent'],
        'success': '#2e7d32' if theme_name == 'Light' else '#4caf50',
        'danger': '#c62828' if theme_name == 'Light' else '#f44336',
        'warning': '#e65100' if theme_name == 'Light' else '#ff9800',
        'neutral': colors['border']
    }


def get_title_bar_widget_style(colors):
    """Return stylesheet for CustomTitleBar widget.
    
    Args:
        colors: Theme colors dictionary
        
    Returns:
        str: Stylesheet for title bar
    """
    return f"""
        CustomTitleBar {{
            background-color: {colors['titlebar_bg']};
            color: {colors['titlebar_fg']};
            border: none;
            margin: 0px;
            padding: 0px;
        }}
        QWidget {{
            background-color: {colors['titlebar_bg']};
            color: {colors['titlebar_fg']};
            border: none;
        }}
    """


def get_title_bar_menu_button_style(colors):
    """Return stylesheet for title bar menu buttons.
    
    Args:
        colors: Theme colors dictionary
        
    Returns:
        str: Stylesheet for menu buttons
    """
    return f"""
        QPushButton {{
            border: none;
            padding: 10px 15px;
            color: {colors['titlebar_fg']};
            background-color: transparent;
            font-size: 12px;
        }}
        QPushButton:hover {{
            background-color: {colors['button_hover']};
        }}
    """


def get_title_bar_search_style(colors):
    """Return stylesheet for title bar search box.
    
    Args:
        colors: Theme colors dictionary
        
    Returns:
        str: Stylesheet for search box
    """
    return f"""
        QLineEdit {{
            background-color: {colors['entry_bg']};
            color: {colors['entry_fg']};
            border: 1px solid {colors['border']};
            padding: 6px 10px;
            border-radius: 4px;
        }}
        QLineEdit:focus {{
            border: 1px solid {colors['accent']};
        }}
    """


def get_title_bar_control_button_style(colors):
    """Return stylesheet template for title bar control buttons (min/max/close).
    
    Args:
        colors: Theme colors dictionary
        
    Returns:
        str: Stylesheet template with %s placeholders for (fg_color, hover_bg)
    """
    return """
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


def get_content_widget_style(colors):
    """Return stylesheet for main content widget.
    
    Args:
        colors: Theme colors dictionary
        
    Returns:
        str: Stylesheet for content widget
    """
    return f"border: none; background-color: {colors['titlebar_bg']}; margin-top: 0px; padding-top: 0px;"


def get_dashboard_widget_style(colors):
    """Return stylesheet for dashboard widget.
    
    Args:
        colors: Theme colors dictionary
        
    Returns:
        str: Stylesheet for dashboard widget
    """
    return f"""
        QWidget#DashboardWidget {{
            background-color: {colors['bg']};
        }}
    """


def get_stat_card_style(colors, accent_color):
    """Return stylesheet for dashboard stat card.
    
    Args:
        colors: Theme colors dictionary
        accent_color: Border/accent color for this card
        
    Returns:
        str: Stylesheet for stat card
    """
    return f"""
        QFrame {{
            border: 2px solid {accent_color};
            border-radius: 8px;
            background-color: {colors['frame_bg']} !important;
            padding: 15px;
        }}
        QLabel {{
            background-color: transparent;
        }}
    """


def get_type_card_style(colors, accent_color):
    """Return stylesheet for dashboard type card.
    
    Args:
        colors: Theme colors dictionary
        accent_color: Border/accent color for this card
        
    Returns:
        str: Stylesheet for type card
    """
    return f"""
        QFrame {{
            border: 1px solid {accent_color};
            border-radius: 5px;
            background-color: {colors['bg']} !important;
            padding: 10px;
        }}
        QLabel {{
            background-color: transparent;
        }}
    """
