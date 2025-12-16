# Vehicle Storage & Voluntary Tow Management System

Desktop application for managing vehicle storage and voluntary tow/transport contracts in Florida. 

## Quick Start

Launch the application:

```bash
python3 lot_gui.py
```

The app supports contract intake, fee templates, payment tracking, and lien timeline management. Data is stored locally in `lot_data.json`.

## Business Licensing Modes

### Default: Voluntary Operations Only (No Wrecker License)

**Current Configuration: `ENABLE_INVOLUNTARY_TOWS = False`**

This mode is designed for businesses that provide **voluntary services only**:

✅ **What You Can Do:**
- **Storage Contracts**: Customers voluntarily store vehicles at your facility
- **Tow/Transport Contracts**: Customer-requested towing services (owner authorization required)
- Standard lien processes for unpaid storage fees
- Florida-compliant fee structures (admin fee capped at $250)

❌ **What You CANNOT Do Without a Wrecker License:**
- Involuntary towing (law enforcement requested)
- Private property impounds
- Abandoned vehicle recovery
- Repo/recovery services
- Use Recovery contract type

### Licensed Mode: Involuntary Towing Enabled

**⚠️ WARNING: Requires valid Florida wrecker license (Chapter 713)**

To enable involuntary towing/recovery features:

1. Open `config.py`
2. Set `ENABLE_INVOLUNTARY_TOWS = True`
3. Update `BUSINESS_LICENSE` with your wrecker license number
4. Restart application

When enabled, adds:
- **Recovery Contracts**: FL 713.78 compliant involuntary towing
- Accelerated lien timeline (7-day notice requirement)
- Vehicle age-based sale eligibility (35-50 days)
- Recovery-specific fees (handling, lien processing, etc.)

## Florida Compliance Features

### Fee Caps (Statutory)
- Admin Fee: $250 maximum (enforced in UI and calculations)
- Lien Processing Fee: $250 maximum
- Combined admin + lien cannot exceed $250

### Tow Contract Storage Exemption
- No storage charge if vehicle on lot < 6 hours (FL allowance)
- Automatic calculation in tow_logic module

### Storage Rate Flexibility
- Daily, weekly, and monthly rates are **independent** (not linear multiples)
- Use actual market rates from fee_templates.json
- Weekly rate ≠ daily × 7; Monthly rate ≠ daily × 30

### Lien Timelines

**Storage Contracts** (voluntary):
- First notice: 30 days
- Second notice: 60 days  
- Lien eligible: 90 days
- Sale eligible: 120 days

**Tow Contracts** (voluntary):
- Payment expected: 7 days
- No lien process (voluntary service agreement)
- Standard collection practices apply

**Recovery Contracts** (involuntary - requires license):
- Notice deadline: 7 business days from storage date
- Sale wait: 35 days (≥3 year old vehicles) or 50 days (<3 years old)
- Minimum notice-to-sale: 30 days

## Architecture

### Module Structure

```
config.py              - Business licensing configuration
lot_models.py          - Data structures (Customer, Vehicle, Contract, etc.)
persistence.py         - All file I/O operations (JSON load/save)
storage_logic.py       - Storage contract business rules
tow_logic.py           - Voluntary tow contract rules (6-hour exemption)
recovery_logic.py      - Involuntary recovery rules (requires license)
lot_logic.py           - Orchestration & routing between modules
lot_gui.py             - PyQt6 user interface (5 tabs)
```

### Configuration-Driven Features

The application routes functionality based on `config.py` flags:

- Contract types available in UI dropdown
- Fee template columns shown/hidden
- Calculation routing (recovery vs storage treatment)
- Lien timeline rules applied

## Data Storage

- **Contracts**: `lot_data.json` (all contract data with full history)
- **Fee Templates**: `fee_templates.json` (6 vehicle types with configurable fees)
- **Backups**: Timestamped copies created via File menu
- **Theme**: `theme_preference.txt` (Dark/Light mode)

## Legal Disclaimer

**⚠️ ALWAYS CONSULT A FLORIDA ATTORNEY** before:
- Enabling involuntary towing features
- Changing lien timelines
- Modifying fee structures
- Processing vehicle sales

This software provides tools for compliance but does not constitute legal advice. 

**Voluntary services only** (default configuration) generally do not require special licensing. **Involuntary towing/recovery services require a Florida wrecker license, proper insurance, and bonding** per Chapter 713 Florida Statutes.

## Support

For questions about:
- **Florida licensing**: Contact FL Department of Highway Safety and Motor Vehicles
- **Legal compliance**: Consult a Florida attorney specializing in Chapter 713
- **Application usage**: See in-app Help menu or contact your software provider
