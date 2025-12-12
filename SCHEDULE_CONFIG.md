# Lien & Sale Schedule Configuration

This document describes the configurable schedules for different contract types. All parameters are defined at the top of `lot_logic.py` for easy adjustment during legal review.

## Tow & Recovery Contracts

**Follows Florida Statute 713.78**

```python
TOW_RECOVERY_SCHEDULE = {
    "lien_notice_deadline_days": 7,      # Must send lien notice within 7 business days
    "sale_wait_days_new_vehicle": 50,    # Vehicles < 3 years old
    "sale_wait_days_old_vehicle": 35,    # Vehicles >= 3 years old
    "min_notice_to_sale_days": 30,       # Minimum days between notice and sale
    "vehicle_age_threshold": 3,          # Age threshold for old vs new
}
```

**Timeline:**
1. Storage begins on `start_date`
2. Lien notice **must** be sent within **7 business days** of storage date
3. If notice sent on time:
   - Lien is immediately eligible
   - Sale eligible after **35 days** (vehicles ≥3 years old) or **50 days** (vehicles <3 years)
   - **Minimum 30 days** enforced between notice and sale
4. If notice sent late or not sent: Lien/sale **invalid**

**Validation:**
- Warns if notice overdue
- Marks sale ineligible if notice sent late
- Calculates vehicle age from `vehicle.year` field
- Enforces 30-day minimum notice-to-sale gap

---

## Storage Only Contracts

**Configurable schedule (slower timeline, pending legal review)**

```python
STORAGE_ONLY_SCHEDULE = {
    "first_notice_days": 30,       # First notice eligibility
    "second_notice_days": 60,      # Second notice eligibility
    "lien_eligible_days": 90,      # Lien eligibility
    "sale_eligible_days": 120,     # Sale eligibility
}
```

**Timeline:**
1. Storage begins on `start_date`
2. First notice eligible after **30 days**
3. Second notice eligible after **60 days**
4. Lien eligible after **90 days**
5. Sale eligible after **120 days**

**Validation:**
- Reminds when notices are recommended (not strict deadlines)
- Provides countdown to lien/sale eligibility
- No strict "invalid" states like Tow & Recovery

---

## Adjusting Schedules

To modify timing parameters for legal compliance:

1. Open `lot_logic.py`
2. Find the schedule dictionaries at the top of the file (around lines 7-27)
3. Adjust the numeric values as needed
4. Save the file
5. Restart the application

**The GUI does not contain any hardcoded dates or timing logic** - all business rules are centralized in `lot_logic.py` for easy auditing and compliance verification.

---

## Function Reference

- **`lien_eligibility(contract, as_of)`** - Returns (is_eligible: bool, status_text: str)
  - Checks contract type and applies appropriate schedule
  - For T&R: Eligible when notice sent on time
  - For Storage: Eligible after configured days

- **`lien_timeline(contract)`** - Returns dict with dates, flags, and warnings
  - Returns different timeline structure based on contract type
  - T&R: Strict validation with notice deadline enforcement
  - Storage: Flexible timeline with recommendation reminders

- **`past_due_status(contract, as_of)`** - Returns (is_past_due: bool, days_past_due: int)
  - Contract-type agnostic, based purely on balance and last payment
