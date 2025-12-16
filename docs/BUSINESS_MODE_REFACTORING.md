# Business Mode Refactoring Summary

**Date**: December 12, 2025  
**Goal**: Configure application for Florida voluntary tow/transport business without wrecker license

## Overview

Refactored the application to enforce voluntary-only operations by default, with Recovery/involuntary towing features hidden behind a licensing configuration flag.

## Changes Made

### 1. Configuration System (`config.py`) ✅

**Created new file** with business licensing controls:

- `ENABLE_INVOLUNTARY_TOWS = False` (default: voluntary operations only)
- `MAX_ADMIN_FEE = 250.00` (Florida statutory cap)
- `MAX_LIEN_FEE = 250.00` (Florida statutory cap)
- `TOW_STORAGE_EXEMPTION_HOURS = 6` (Florida allowance for short-term storage)
- Business info fields (name, address, phone, license)
- Comprehensive compliance notes explaining licensing requirements

### 2. Tow Logic Updates (`tow_logic.py`) ✅

**6-Hour Storage Exemption**:
- Modified `calculate_tow_storage_fees()` to check time on lot
- Returns `0.0` if vehicle on lot < 6 hours (Florida exemption)
- Only charges storage after exemption period expires

### 3. Core Business Logic (`lot_logic.py`) ✅

**Config Integration**:
- Added imports: `ENABLE_INVOLUNTARY_TOWS`, `MAX_ADMIN_FEE`, `MAX_LIEN_FEE`
- Updated `is_recovery_type()`: Returns `False` when flag disabled
- Updated `calculate_charges()`: Routes to storage logic when recovery disabled
- Updated `lien_timeline()`: Treats disabled recovery as storage
- Replaced hardcoded `250.00` caps with `MAX_ADMIN_FEE` and `MAX_LIEN_FEE` constants

**Fee Cap Enforcement**:
- All admin fees automatically capped at `MAX_ADMIN_FEE` ($250)
- Consistent enforcement across all contract types

### 4. Recovery Logic Guards (`recovery_logic.py`) ✅

**License Requirement Warnings**:
- Added prominent warning in module docstring
- Added config imports: `ENABLE_INVOLUNTARY_TOWS`, `MAX_ADMIN_FEE`, `MAX_LIEN_FEE`
- Modified `calculate_recovery_fees()`: Returns `0.0` if not enabled
- Prevents accidental use of recovery features without licensing

### 5. GUI Updates (`lot_gui.py`) ✅

**Contract Type Restrictions**:
- Intake form: Only shows "Storage" and "Tow" by default
- "Recovery" option only appears if `ENABLE_INVOLUNTARY_TOWS = True`
- Contracts filter: Conditionally includes Recovery in dropdown
- Prevents creating recovery contracts when not licensed

**Fee Template UI**:
- Dynamic column display based on `ENABLE_INVOLUNTARY_TOWS`
- Shows 8 columns (voluntary) or 14 columns (with recovery)
- Warning banner when involuntary towing disabled
- Column order: Vehicle Type → Storage → Tow → [Recovery if enabled] → Admin/Labor

**Fee Validation**:
- `validate_admin_fee()`: Uses `MAX_ADMIN_FEE` constant
- `validate_lien_fee()`: Uses `MAX_LIEN_FEE` constant
- `save_fee_templates_action()`: Validates admin fee doesn't exceed cap
- Real-time visual feedback (red borders) for violations

### 6. Documentation (`README.md`) ✅

**Comprehensive Rewrite**:
- Business licensing modes explained (voluntary vs. licensed)
- Clear list of what you CAN and CANNOT do without license
- Instructions for enabling involuntary features (if licensed)
- Florida compliance features documented:
  - Fee caps ($250)
  - 6-hour tow storage exemption
  - Independent storage rates (not linear multiples)
  - Lien timelines by contract type
- Architecture overview with module descriptions
- Legal disclaimer emphasizing attorney consultation

## Contract Type Behavior

### Storage (Always Available)
- Customer voluntarily stores vehicle
- Daily/weekly/monthly storage fees
- Admin fee (max $250)
- Lien timeline: 30/60/90/120 days
- No special licensing required

### Tow (Always Available)
- Voluntary tow service (customer authorized)
- Base/hook fee + mileage + labor
- After-hours surcharge option
- Storage fees (after 6-hour exemption)
- Admin fee (max $250)
- 7-day payment expectation
- No lien process (voluntary service)
- No special licensing required

### Recovery (Requires License) ⚠️
- **HIDDEN BY DEFAULT** (`ENABLE_INVOLUNTARY_TOWS = False`)
- Involuntary towing (law enforcement, impounds)
- Florida Statute 713.78 compliance
- 7-day notice requirement
- 35-50 day sale timeline (vehicle age dependent)
- Recovery handling + lien processing fees
- **Requires valid FL wrecker license**

## Fee Structure Enforcement

### Florida Statutory Caps
```python
MAX_ADMIN_FEE = 250.00   # Per Florida law
MAX_LIEN_FEE = 250.00    # Per Florida law
```

### Storage Rate Independence
- Daily, weekly, monthly rates are **independent values**
- Not calculated as linear multiples (daily × 7 ≠ weekly)
- Uses actual values from `fee_templates.json`
- Reflects real market pricing

### Tow-Specific Rules
- **6-hour exemption**: No storage charge if on lot < 6 hours
- Calculated automatically in `tow_logic.calculate_tow_storage_fees()`
- After exemption: Standard storage rates apply

## File Changes Summary

| File | Status | Description |
|------|--------|-------------|
| `config.py` | ✅ Created | Business licensing configuration |
| `tow_logic.py` | ✅ Updated | 6-hour storage exemption |
| `lot_logic.py` | ✅ Updated | Config routing, fee cap constants |
| `recovery_logic.py` | ✅ Updated | License requirement guards |
| `lot_gui.py` | ✅ Updated | Conditional UI, fee validation |
| `README.md` | ✅ Rewritten | Licensing modes, compliance docs |

## Testing Results ✅

Application launched successfully with:
- Contract types: Storage, Tow (Recovery hidden)
- Fee templates: 8 columns (no recovery columns)
- Admin fee validation: $250 cap enforced
- No errors or warnings

## Migration Notes

### For Existing Users

**No data migration required**. Existing contracts remain intact:

- Storage contracts: Continue working normally
- Tow contracts: Continue working normally
- Recovery contracts (if any): Treated as storage contracts when `ENABLE_INVOLUNTARY_TOWS = False`

### Enabling Licensed Mode

To enable recovery features (requires proper licensing):

1. Open `config.py`
2. Change: `ENABLE_INVOLUNTARY_TOWS = False` → `True`
3. Update: `BUSINESS_LICENSE = "FL-XXXXX"` (your license number)
4. Verify: Proper insurance and bonding in place
5. Restart application
6. Result: Recovery appears in dropdowns, fee templates show recovery columns

## Compliance Checklist

✅ Voluntary operations require no special license  
✅ Admin fees capped at $250 (Florida requirement)  
✅ 6-hour storage exemption for tow contracts  
✅ Independent storage rates (not linear multiples)  
✅ Recovery features disabled without license  
✅ No way to accidentally create recovery contracts  
✅ Clear warnings in code and documentation  

⚠️ **ALWAYS CONSULT A FLORIDA ATTORNEY** before enabling involuntary towing features

## Support Resources

- **Florida Licensing**: FL DHSMV (Chapter 713)
- **Legal Compliance**: Florida attorney specializing in vehicle storage law
- **Application Help**: In-app Help menu

---

**End of Refactoring Summary**
