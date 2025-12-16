# Application Settings Documentation

## Overview
The application now includes a comprehensive settings system accessible from **Help → Settings**.

Settings are automatically saved to `data/app_settings.json` and persist across application restarts.

## Settings Categories

### 1. Appearance
- **Color Scheme**: Choose from 7 themes
  - Dark (default)
  - Light
  - Blue Dark
  - Green Dark
  - Purple Dark
  - Warm Light
  - Cool Light

### 2. Display
- **Font Size**: Small / Medium / Large *(requires restart)*
- **Date Format**: MM/DD/YYYY, DD/MM/YYYY, or YYYY-MM-DD
- **Time Format**: 12-hour or 24-hour
- **Compact Mode**: Reduce spacing for more data on screen *(requires restart)*

### 3. Behavior
- **Auto-save Interval**: 1-60 minutes (default: 5 minutes)
- **Confirm Before Delete**: Safety confirmation for contract deletions
- **Show Tooltips**: Display helpful hints throughout the application
- **Startup Tab**: Which tab to show on application launch
  - Dashboard (default)
  - Intake
  - Contracts
  - Yard View

### 4. Alerts
- **Auto-check Frequency**: 0-120 minutes (0 = manual only, default: 30)
- **Desktop Notifications**: Show system notifications for urgent alerts
- **Alert Sound**: Play audio notification when alerts are found

### 5. Backup
- **Auto-backup**: Never / Daily / Weekly (default: Daily)
- **Backup Location**: Folder path for automated backups
- **Keep Records For**: 0-3650 days (0 = forever, default: 365)

### 6. Defaults
Pre-fill forms with common values to speed up data entry:
- **Default Vehicle Type**: Car / Truck / Motorcycle / RV / Boat / Trailer
- **Default Payment Method**: Cash / Check / Card / Money Order / Wire Transfer
- **Default Admin Fee**: Leave empty to use fee template value

### 7. Business Info
Appears on forms, reports, and lien notices:
- **Business Name**
- **Address**
- **Phone**
- **Email**
- **Logo**: Upload company logo for professional documents

### 8. Reports
- **Include Photos in Reports**: Add vehicle photos to generated reports
- **Report Footer Text**: Custom text appearing at bottom of all reports

## Usage

### Opening Settings
1. Click **Help** in the menu bar
2. Select **⚙️ Settings**

### Applying Changes
- **Apply**: Preview changes immediately without closing the dialog
- **OK**: Save changes and close
- **Cancel**: Discard changes and close

### Resetting Settings
Click **Reset to Defaults** to restore all settings to their original values. You will be prompted to confirm this action.

## Technical Details

### Storage Location
- Settings file: `data/app_settings.json`
- Format: JSON with human-readable structure
- Automatically created on first run

### Theme Application
Theme changes apply immediately via the **Apply** button. The dialog updates its appearance to match the selected theme for instant preview.

### Settings Manager
The `SettingsManager` class (`utils/settings_manager.py`) handles:
- Loading settings from file
- Merging with defaults (ensures new settings appear after updates)
- Saving settings to file
- Providing get/set methods for accessing settings

### Integration Points
Settings are accessed throughout the application via:
```python
self.settings_manager.get('setting_name', default_value)
```

Future features can easily add new settings by:
1. Adding default value in `SettingsManager._get_defaults()`
2. Adding UI control in appropriate settings tab
3. Loading/saving in `load_current_settings()` / `save_current_settings()`
4. Using the setting value in application logic

## Notes

### Font Size & Compact Mode
Changes to font size and compact mode require restarting the application to take full effect due to PyQt6 rendering requirements.

### Business Logo
Supported image formats:
- PNG (recommended for transparency)
- JPG/JPEG
- BMP
- GIF

Logo is automatically resized to fit forms and reports while maintaining aspect ratio.

### Auto-save
Auto-save operates independently of the backup system. It saves the current database state at the specified interval while you work.

### Backup Location
If the specified backup location doesn't exist or isn't writable, backups will fall back to the default location: `Documents/LotBackups/`
