# UI Styling Architecture

## Overview
All UI styling is now centralized in `theme_config.py` for easy maintenance and modification.

## File Structure

### theme_config.py
**Purpose**: Single source of truth for all colors and styling
**Location**: `/home/sniper/Desktop/storage lot program/theme_config.py`

**Key Functions**:
1. `get_theme_colors(theme_name)` - Returns color dictionary for "Dark" or "Light" theme
2. `get_application_stylesheet(colors)` - Generates complete CSS stylesheet

### lot_gui.py  
**Purpose**: Application logic and UI components
**Styling**: Imports and uses theme_config functions
**Note**: NO hardcoded THEMES dictionary - removed for clean separation

## Current Tab Configuration

### Tab Names (as of restructure):
1. **First Tab**: "Contracts" (overview/dashboard)
2. **Second Tab**: "Dashboard" (full list view)
3. Additional tabs: "Intake", "Reports", "Fee Templates"

### Tab Styling (in theme_config.py):
```python
QTabWidget::pane {
    border: 0;              # NO BORDER - prevents white line
    background: [color];
    margin: 0;
    padding: 0;
}

QTabBar {
    border: 0;              # NO BORDER
}

QTabBar::tab {
    background: [color];
    color: [color];
    padding: 10px 20px;
    margin: 0;
    border: 0;              # NO BORDER on tabs
}

QTabBar::tab:selected {
    background: [color];
    font-weight: bold;
    # NO border-bottom - this was causing the white line
}
```

## How to Modify Styling

### Change Tab Appearance:
1. Open `theme_config.py`
2. Find `QTabBar::tab` section in `get_application_stylesheet()`
3. Modify padding, colors, borders, etc.
4. Save file
5. **Clear Python cache**: `find . -name "*.pyc" -delete; rm -rf __pycache__`
6. Restart application

### Change Colors:
1. Open `theme_config.py`
2. Modify `get_theme_colors()` function
3. Update Dark or Light theme dictionaries
4. Available color keys:
   - bg, fg (background/foreground)
   - frame_bg, frame_fg
   - input_bg, input_fg
   - button_bg, button_fg, button_hover
   - header_bg
   - titlebar_bg, titlebar_fg
   - entry_bg, entry_fg
   - select_bg, select_fg
   - tree_odd, tree_even
   - accent, border

### Add New Theme:
1. In `get_theme_colors()`, add new `elif` branch
2. Return dictionary with all required color keys
3. Update theme selection logic in lot_gui.py

## Troubleshooting

### Changes Not Appearing:
1. **Clear cache**: `find . -name "*.pyc" -delete; rm -rf __pycache__`
2. **Kill all instances**: `pkill -f lot_gui.py`
3. **Wait**: `sleep 1`
4. **Restart**: `python3 lot_gui.py`

### White Line Under Tabs:
- Caused by `border-bottom` on `QTabBar::tab:selected`
- **Solution**: Remove ALL border properties from tab styling
- Location: `theme_config.py` line ~76

### Tab Names Wrong:
- Check `addTab()` calls in lot_gui.py:
  - Line ~671: First tab creation
  - Line ~1125: Second tab creation  
  - Line ~975: Dashboard refresh insert

### Theme Not Loading:
- Verify `from theme_config import get_theme_colors, get_application_stylesheet`
- Check `apply_theme()` method calls `get_application_stylesheet(colors)`
- Ensure `self.setStyleSheet(stylesheet)` is called

## Testing

Run theme test:
```bash
cd "/home/sniper/Desktop/storage lot program"
python3 test_theme.py
```

Should output:
- ✓ Theme configuration loaded
- ✓ Stylesheet generated
- ✓ Tab styling found

## Benefits of New Structure

1. **Single Source**: All styling in one file
2. **Easy Maintenance**: Change colors/styles in one place
3. **Consistent**: No conflicting style definitions
4. **Testable**: Can verify theme config independently
5. **Clean Separation**: UI logic separate from styling
6. **Version Control**: Easy to track styling changes

## Migration Notes

**Removed from lot_gui.py**:
- Old THEMES dictionary (lines 34-73)
- Hardcoded color values scattered through code
- Duplicate styling definitions

**Centralized in theme_config.py**:
- All color definitions
- Complete application stylesheet
- Tab widget styling
- Button styling  
- Table styling
- Input field styling
- All UI component styles
