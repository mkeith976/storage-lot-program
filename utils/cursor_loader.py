"""Load custom cursors from system cursor theme."""
import os
from pathlib import Path
from PyQt6.QtGui import QCursor, QPixmap
from PyQt6.QtCore import Qt, QPoint


def get_cursor_theme_paths():
    """Get possible cursor theme directories."""
    paths = []
    
    # Check common cursor theme locations
    home = Path.home()
    
    # User cursor themes
    paths.append(home / ".icons")
    paths.append(home / ".local/share/icons")
    
    # System cursor themes
    paths.extend([
        Path("/usr/share/icons"),
        Path("/usr/share/pixmaps"),
        Path("/usr/local/share/icons"),
    ])
    
    return [p for p in paths if p.exists()]


def find_cursor_theme():
    """Find the active cursor theme name."""
    # Try to read cursor theme from various config files
    home = Path.home()
    
    # Check GTK settings
    gtk3_config = home / ".config/gtk-3.0/settings.ini"
    if gtk3_config.exists():
        try:
            content = gtk3_config.read_text()
            for line in content.split('\n'):
                if 'gtk-cursor-theme-name' in line and '=' in line:
                    theme = line.split('=')[1].strip().strip('"').strip("'")
                    if theme:
                        return theme
        except:
            pass
    
    # Check X resources
    xresources = home / ".Xresources"
    if xresources.exists():
        try:
            content = xresources.read_text()
            for line in content.split('\n'):
                if 'Xcursor.theme' in line and ':' in line:
                    theme = line.split(':')[1].strip()
                    if theme:
                        return theme
        except:
            pass
    
    # Default fallback themes
    return os.environ.get('XCURSOR_THEME', 'default')


def load_cursor_from_theme(cursor_name, theme_name=None, size=24):
    """
    Load a cursor image from the system cursor theme.
    
    Args:
        cursor_name: Name of cursor (e.g., 'size_ver', 'size_hor', 'size_fdiag', 'size_bdiag')
        theme_name: Name of cursor theme (auto-detect if None)
        size: Cursor size in pixels
    
    Returns:
        QCursor or None if not found
    """
    if theme_name is None:
        theme_name = find_cursor_theme()
    
    # Possible cursor file names for each type
    cursor_variants = {
        'size_ver': ['sb_v_double_arrow', 'size_ver', 'v_double_arrow', 'split_v', 'row-resize', 'ns-resize'],
        'size_hor': ['sb_h_double_arrow', 'size_hor', 'h_double_arrow', 'split_h', 'col-resize', 'ew-resize'],
        'size_fdiag': ['size_fdiag', 'fd_double_arrow', 'nwse-resize'],
        'size_bdiag': ['size_bdiag', 'bd_double_arrow', 'nesw-resize'],
        'top_left_corner': ['top_left_corner', 'nw-resize'],
        'top_right_corner': ['top_right_corner', 'ne-resize'],
        'bottom_left_corner': ['bottom_left_corner', 'sw-resize'],
        'bottom_right_corner': ['bottom_right_corner', 'se-resize'],
    }
    
    variants = cursor_variants.get(cursor_name, [cursor_name])
    
    # Search for cursor in theme paths
    for base_path in get_cursor_theme_paths():
        theme_path = base_path / theme_name / "cursors"
        
        if not theme_path.exists():
            continue
        
        # Try each variant
        for variant in variants:
            cursor_file = theme_path / variant
            
            if cursor_file.exists():
                try:
                    # Try to load as X11 cursor using QCursor
                    # Note: This may not work for all cursor formats
                    pixmap = QPixmap(str(cursor_file))
                    if not pixmap.isNull():
                        # Calculate hotspot (center of cursor)
                        hotspot = QPoint(pixmap.width() // 2, pixmap.height() // 2)
                        return QCursor(pixmap, hotspot.x(), hotspot.y())
                except:
                    pass
    
    return None


def get_resize_cursors():
    """
    Get all resize cursors from system theme.
    
    Returns:
        dict mapping cursor type to QCursor, or None if system cursors couldn't be loaded
    """
    cursors = {}
    cursor_types = ['size_ver', 'size_hor', 'size_fdiag', 'size_bdiag']
    
    for cursor_type in cursor_types:
        cursor = load_cursor_from_theme(cursor_type)
        if cursor:
            cursors[cursor_type] = cursor
    
    # Only return cursors if we got all of them
    if len(cursors) == len(cursor_types):
        return cursors
    
    return None
