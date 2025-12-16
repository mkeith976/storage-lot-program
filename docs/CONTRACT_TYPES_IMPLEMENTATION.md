# Contract Type System Update - Implementation Summary

## Overview
Updated the Storage & Recovery Lot system to support three distinct contract types with improved fee structures and Florida compliance rules.

## Contract Types

### 1. Storage (Internal: "storage")
- Basic storage with flexible rate modes
- No tow or recovery fees
- Simple fee structure

### 2. Tow (Internal: "tow") 
- Voluntary tow service contracts
- Owner-requested tows
- Includes tow base fee, mileage, labor, and after-hours fees
- Storage fee not applied if vehicle on lot < 6 hours (FL rule)
- Admin fee capped at $250 (FL rule)

### 3. Recovery (Internal: "recovery")
- Involuntary recovery contracts  
- Includes recovery handling, lien processing, certified mail, title search, DMV, and sale fees
- Lien processing fee capped at $250 (FL rule)
- Storage fee not applied if vehicle on lot < 6 hours (FL rule)
- Subject to Florida 713.78 lien timing rules

## Storage Rate Modes

All contract types support three rate modes:
- **Daily**: Charges per day using `daily_storage_fee`
- **Weekly**: Charges per week (days/7) using `weekly_storage_fee`
- **Monthly**: Charges per month (days/30) using `monthly_storage_fee`

## Fee Structure Changes

### Data Model (lot_models.py - StorageContract)

**New Fields Added:**
```python
# Storage rate fields
rate_mode: str = "daily"  # "daily", "weekly", or "monthly"
daily_storage_fee: float = 0.0
weekly_storage_fee: float = 0.0
monthly_storage_fee: float = 0.0

# Tow contract fields (voluntary)
tow_mileage_rate: float = 0.0
tow_miles_used: float = 0.0
tow_hourly_labor_rate: float = 0.0
tow_labor_hours: float = 0.0
tow_after_hours_fee: float = 0.0

# Recovery contract fields (involuntary)
recovery_handling_fee: float = 0.0
lien_processing_fee: float = 0.0
cert_mail_fee: float = 0.0
title_search_fee: float = 0.0
dmv_fee: float = 0.0
sale_fee: float = 0.0
notices_sent: int = 0
```

### Business Logic (lot_logic.py)

**Helper Functions:**
- `is_recovery_type(contract)` - Checks if contract is recovery/tow & recovery
- `is_tow_type(contract)` - Checks if contract is voluntary tow
- `is_storage_type(contract)` - Checks if contract is storage only

**Updated calculate_charges():**
- Calculates storage based on rate_mode (daily/weekly/monthly)
- Enforces 6-hour rule: No storage fee if vehicle on lot < 6 hours
- Handles tow fees: base + (mileage_rate × miles) + (labor_rate × hours) + after_hours
- Handles recovery fees: handling + lien (max $250) + (cert_mail × notices) + title + DMV + sale
- Enforces admin fee cap at $250 for all contract types

**Fee Templates:**
All vehicle types (Car, Truck, Motorcycle, RV, Boat, Trailer) now include:
- `daily_storage_fee`, `weekly_storage_fee`, `monthly_storage_fee`
- `tow_base_fee`, `tow_mileage_rate`, `tow_hourly_labor_rate`, `after_hours_fee`
- `recovery_handling_fee`, `lien_processing_fee`, `cert_mail_fee`
- `title_search_fee`, `dmv_fee`, `sale_fee`
- `admin_fee`, `labor_rate`

### User Interface (lot_gui.py)

**Intake Form Changes:**
1. **Contract Type at Top** - Moved to first field with options: Storage, Tow, Recovery
2. **Storage Rate Mode** - Dropdown with Daily/Weekly/Monthly options
3. **Storage Fee Fields** - Daily, Weekly, and Monthly fee inputs
4. **Tow Section** - Shows/hides based on contract type:
   - Tow Base Fee
   - Tow Mileage Rate
   - Tow Miles Used
   - Tow Hourly Labor Rate
   - Tow Labor Hours
   - After Hours Fee
5. **Recovery Section** - Shows/hides based on contract type:
   - Recovery Handling Fee
   - Lien Processing Fee (max $250)
   - Certified Mail Fee (per notice)
   - Notices Sent (count)
   - Title Search Fee
   - DMV Fee
   - Sale Fee

**Fee Templates Tab:**
Expanded to 17 columns showing all configurable fees:
1. Vehicle Type
2. Daily Storage
3. Weekly Storage
4. Monthly Storage
5. Tow Base
6. Tow Mileage Rate
7. Tow Labor Rate
8. After Hours
9. Recovery Handling
10. Lien Processing
11. Cert Mail
12. Title Search
13. DMV Fee
14. Sale Fee
15. Admin Fee
16. Labor Rate
17. Legacy Daily Rate (for backward compatibility)

## Florida Compliance Rules

**Enforced in calculate_charges():**
- ✓ No storage charges if vehicle on lot < 6 hours
- ✓ Admin fee capped at $250
- ✓ Lien processing fee capped at $250

**Warnings Generated (does not block contract creation):**
- Admin fee > $250
- Lien processing fee > $250

**Lien Timing (Florida 713.78):**
- Recovery/Tow & Recovery contracts follow strict 7-day notice deadline
- Lien notice must be sent within 7 business days
- Sale eligibility based on vehicle age (35 or 50 days)
- Storage/Tow contracts follow more lenient schedule

## Backward Compatibility

**Legacy Fields Preserved:**
- `daily_rate` (maps to `daily_storage_fee` for compatibility)
- `tow_fee`, `impound_fee`, `admin_fee`
- `tow_base_fee`, `mileage_included`, `mileage_rate`
- `certified_mail_fee_first`, `certified_mail_fee_second`
- `extra_labor_minutes`, `labor_rate_per_hour`, `recovery_miles`

**Contract Type Mapping:**
- Old "Storage Only" → "storage"
- Old "Tow & Recovery" → "recovery"
- New "Tow" → "tow"

**Legacy Contracts:**
- Existing contracts load without errors
- Missing new fields default to 0
- Old calculation logic preserved for contracts without new fields

## Testing

All files compile successfully:
```bash
python3 -m py_compile lot_gui.py lot_logic.py lot_models.py
```

Application launches without errors and displays:
- Updated intake form with contract type selector
- Dynamic show/hide for Tow and Recovery sections
- Expanded fee templates table
- All existing features intact (themes, search, contract list, etc.)

## Key Implementation Details

**Dynamic Form Fields:**
- Tow section visible only when Contract Type = "Tow"
- Recovery section visible only when Contract Type = "Recovery"
- Storage rate fields always visible for all types

**Fee Calculation Priority:**
1. Check contract type (storage/tow/recovery)
2. Calculate storage based on rate_mode
3. Add type-specific fees (tow or recovery)
4. Apply caps (admin $250, lien $250)
5. Enforce 6-hour rule for storage

**Data Flow:**
1. User selects contract type → Form updates
2. User fills fields → Values stored in contract
3. Contract saved → calculate_charges() applies rules
4. Balance displayed → Reflects correct fees per type

## File Changes Summary

- **lot_models.py**: Added 13 new fields to StorageContract dataclass
- **lot_logic.py**: 
  - Updated DEFAULT_VEHICLE_FEES with 11 new fee types
  - Added 3 helper functions for contract type checking
  - Rewrote calculate_charges() for multi-type support
  - Updated load_fee_templates() for dynamic field loading
- **lot_gui.py**:
  - Rebuilt intake form with contract type selector at top
  - Added storage rate mode selector
  - Added conditional Tow and Recovery sections
  - Expanded fee templates table to 17 columns
  - Updated save/load logic for all new fields
  - Added Florida rule warnings (non-blocking)

All changes maintain existing UI features, themes, and functionality while adding the new contract type system.
