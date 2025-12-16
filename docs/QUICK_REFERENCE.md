# Quick Reference: Voluntary vs. Licensed Mode

## Current Configuration

```python
# config.py
ENABLE_INVOLUNTARY_TOWS = False  # ← VOLUNTARY MODE (Default)
```

## What This Means

### ✅ YOU CAN DO (No License Required)

**Storage Contracts**
- Customer voluntarily stores their vehicle
- Daily/weekly/monthly storage fees
- Standard lien process if unpaid (90+ days)
- Admin fee up to $250

**Tow Contracts** 
- Customer requests tow service
- Customer owns vehicle or has authority
- Base tow fee + mileage + labor
- No storage charge if < 6 hours on lot
- After-hours fees allowed
- Admin fee up to $250
- 7-day payment expectation

### ❌ YOU CANNOT DO (Requires Wrecker License)

- Law enforcement requested tows
- Private property impounds
- Abandoned vehicle recovery
- Repo/recovery services
- Accelerated lien timeline (7-day notice)
- Recovery-specific fees

## How to Enable Licensed Mode

**⚠️ ONLY IF YOU HAVE A VALID FLORIDA WRECKER LICENSE**

1. Open `config.py`
2. Change line 21:
   ```python
   ENABLE_INVOLUNTARY_TOWS = True  # ← Enable recovery features
   ```
3. Update line 60:
   ```python
   BUSINESS_LICENSE = "FL-YOUR-LICENSE-NUMBER"
   ```
4. Save file
5. Restart application
6. Verify "Recovery" appears in Contract Type dropdown

## Key Features by Mode

| Feature | Voluntary Mode | Licensed Mode |
|---------|---------------|---------------|
| Storage contracts | ✅ | ✅ |
| Tow contracts | ✅ | ✅ |
| Recovery contracts | ❌ | ✅ |
| Admin fee cap | $250 | $250 |
| 6-hour tow exemption | ✅ | ✅ |
| Storage lien timeline | 90 days | 90 days |
| Recovery lien timeline | N/A | 7 days |
| Fee template columns | 8 columns | 14 columns |

## Florida Fee Caps (Both Modes)

```python
MAX_ADMIN_FEE = 250.00      # Statutory cap
MAX_LIEN_FEE = 250.00       # Statutory cap
TOW_STORAGE_EXEMPTION_HOURS = 6  # No charge if < 6 hours
```

## Contract Type Quick Guide

### STORAGE
- **Use for**: Customer storing vehicle voluntarily
- **Fees**: Storage (daily/weekly/monthly) + Admin ($250 max)
- **Lien**: 30/60/90/120 day timeline
- **License**: None required

### TOW
- **Use for**: Customer requested tow/transport
- **Fees**: Base + Mileage + Labor + After-hours + Storage (after 6 hrs) + Admin ($250 max)
- **Lien**: None (voluntary service)
- **License**: None required

### RECOVERY (if enabled)
- **Use for**: Involuntary towing (law enforcement, impounds)
- **Fees**: All tow fees + Recovery handling + Lien processing + Cert mail + Title/DMV + Sale
- **Lien**: FL 713.78 (7-day notice, 35-50 day sale)
- **License**: ⚠️ **REQUIRES FL WRECKER LICENSE**

## Need Help?

**Enabling Licensed Mode**
→ See `BUSINESS_MODE_REFACTORING.md` "Enabling Licensed Mode" section

**Florida Licensing Questions**
→ Contact FL Department of Highway Safety and Motor Vehicles

**Legal Compliance**
→ Consult a Florida attorney specializing in Chapter 713

**Application Usage**
→ See Help menu in application or `README.md`
