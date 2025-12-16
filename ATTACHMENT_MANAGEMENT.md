# Attachment Management Feature

## Overview
You can now attach documents, images, and videos to any contract record for easy reference and documentation.

## Features

### Supported File Types
- **Images**: JPG, JPEG, PNG, GIF, BMP, WebP
- **Documents**: PDF, DOC, DOCX, TXT, RTF
- **Videos**: MP4, MOV, AVI, MKV, WMV, FLV
- **Spreadsheets**: XLS, XLSX, CSV
- **Audio**: MP3, WAV, FLAC, AAC
- **Archives**: ZIP, RAR, 7Z, TAR, GZ
- **Any other file type** you need!

## How to Use

### Accessing Attachments
1. **From Contracts Tab**: Select a contract and either:
   - Right-click → **"📎 Manage Attachments..."**
   - Edit menu → **"Manage Attachments..."**

### Adding Attachments
1. Click **"➕ Add Files..."** button
2. Browse and select one or more files
3. Files are automatically:
   - Copied to `attachments/contract_[ID]/` directory
   - Linked to the contract
   - Logged in audit trail

### Viewing Attachments
1. Select an attachment from the list
2. Click **"👁️ View/Open"** button
3. File opens with your system's default application
   - Images open in image viewer
   - PDFs open in PDF reader
   - Videos open in video player
   - etc.

### Removing Attachments
1. Select an attachment from the list
2. Click **"🗑️ Remove"** button
3. Confirm removal
   - File remains in attachments folder
   - Link to contract is removed
   - Change is logged in audit trail

## File Organization

### Directory Structure
```
attachments/
├── contract_1/
│   ├── photo_front.jpg
│   ├── photo_rear.jpg
│   ├── invoice.pdf
│   └── video_damage.mp4
├── contract_2/
│   ├── document.pdf
│   └── image.png
...
```

### Features
- **Automatic Organization**: Each contract gets its own subfolder
- **Duplicate Handling**: If you upload a file with the same name, it's automatically renamed (e.g., `photo_1.jpg`, `photo_2.jpg`)
- **File Preservation**: Removing an attachment from a contract doesn't delete the file - it stays in the folder for your records

## File Information Display

Each attachment shows:
- **Icon** indicating file type (🖼️ for images, 🎬 for videos, 📕 for PDFs, etc.)
- **Filename**
- **File size** in human-readable format (KB, MB, GB)

Example:
```
🖼️ vehicle_front.jpg (2.3 MB)
📕 insurance_claim.pdf (456.7 KB)
🎬 damage_video.mp4 (15.8 MB)
```

## Audit Trail

All attachment changes are automatically logged:
- **When Added**: `[2025-12-14 12:30:45] Attachment Added - File: vehicle_photo.jpg`
- **When Removed**: `[2025-12-14 13:45:22] Attachment Removed - File: old_document.pdf`

## Use Cases

### Common Attachments
- **Vehicle Photos**: Front, rear, sides, damage close-ups
- **Insurance Documents**: Claim forms, policies, correspondence
- **Tow Authorization**: Signed authorization forms
- **Inspection Reports**: Condition reports, damage assessments
- **Owner Communication**: Emails, letters, text message screenshots
- **Invoices**: Tow invoices, storage invoices, repair quotes
- **Lien Documents**: Notice copies, certified mail receipts
- **Videos**: Walk-around videos, damage documentation

### Best Practices
1. **Take photos immediately** when vehicle arrives
2. **Document all damage** with close-up photos
3. **Scan and attach** all paper documents
4. **Keep authorization forms** for voluntary tows
5. **Save communication** with owners
6. **Attach lien notice copies** for recovery contracts

## Technical Details

### File Storage
- Files are **copied** to the application's `attachments/` directory
- Original files remain in their source location
- Each contract has a dedicated subdirectory: `attachments/contract_[ID]/`

### Security
- Files are stored locally on your computer
- Only file paths are stored in the database (JSON)
- Removing a contract doesn't delete attachments (manual cleanup required if desired)

### Platform Compatibility
- **Windows**: Opens with default Windows applications
- **macOS**: Opens with default macOS applications
- **Linux**: Opens with xdg-open (uses system defaults)

## Tips

💡 **Organization Tip**: Use descriptive filenames like `vehicle_front.jpg`, `damage_left_fender.jpg` instead of generic names like `IMG_001.jpg`

💡 **Storage Tip**: Large video files (>50MB) should be compressed before attaching to save disk space

💡 **Documentation Tip**: Add attachments right when the vehicle arrives - don't wait until later when you might forget details

💡 **Backup Tip**: The auto-backup feature backs up the contract data but not attachments. Periodically backup the entire `attachments/` folder separately

## Troubleshooting

### File Not Found Error
- **Cause**: Attachment file was moved or deleted outside the application
- **Solution**: Re-add the file or remove the broken attachment link

### Can't Open File
- **Cause**: No application installed to handle that file type
- **Solution**: Install appropriate software (e.g., PDF reader for PDFs, video player for videos)

### Large Files Slow
- **Cause**: Very large video files (>100MB)
- **Solution**: Compress videos before attaching, or use shorter video clips

---

**Feature Added:** December 14, 2025  
**Version:** 1.0  
**Status:** ✅ Production Ready
