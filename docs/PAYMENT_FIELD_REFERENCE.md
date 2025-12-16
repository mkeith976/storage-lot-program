# Payment Field Quick Reference

## ✅ CORRECT Usage

### Creating a Payment
```python
from lot_models import Payment

payment = Payment(
    date="2025-12-12",
    amount=100.0,
    method="cash",
    note="Payment note here"  # ✓ 'note' (singular)
)
```

### Reading Payment Data
```python
# Accessing the note field
if payment.note:
    print(f"Payment note: {payment.note}")  # ✓ 'note' (singular)
```

### In GUI Code
```python
# Creating payment from form
payment = Payment(
    date=datetime.today().strftime("%Y-%m-%d"),
    amount=amount,
    method=method_combo.currentText(),
    note=notes_input.text()  # ✓ 'note' (singular)
)

# Displaying payment in receipt
if payment.note:
    receipt += f"Notes: {payment.note}\n"  # ✓ 'note' (singular)
```

## ❌ INCORRECT Usage

### DO NOT Use 'notes' (plural)
```python
# ❌ WRONG - will be ignored or cause AttributeError
payment = Payment(
    date="2025-12-12",
    amount=100.0,
    method="cash",
    notes="This won't work"  # ❌ Wrong field name
)

# ❌ WRONG - AttributeError on Payment objects
if payment.notes:  # ❌ No such attribute
    print(payment.notes)
```

## Backward Compatibility

Old JSON files with `notes` field are automatically migrated:

```json
// Old format (still loads correctly)
{
  "date": "2025-12-12",
  "amount": 100.0,
  "method": "cash",
  "notes": "Legacy format"  // ← Automatically converted to 'note'
}

// New format (preferred)
{
  "date": "2025-12-12", 
  "amount": 100.0,
  "method": "cash",
  "note": "Current format"  // ← Use this
}
```

## Field Name Rules

| Class | Field Name | Type | Notes |
|-------|-----------|------|-------|
| Payment | `note` | str | **Singular** - Use `note` not `notes` |
| Notice | `notes` | str | **Plural** - Use `notes` not `note` |
| StorageContract | `notes` | List[str] | **Plural** - List of note strings |

## Testing

Verify payment field usage:
```bash
# Run comprehensive tests
python3 test_payment_field.py

# Search for incorrect usage
grep -r "payment\.notes" .  # Should find none in active code
grep -r 'notes=' . | grep Payment  # Should find none in active code
```

## Common Mistakes

### Mistake 1: Using 'notes' in Payment constructor
```python
# ❌ WRONG
payment = Payment(notes="text")

# ✅ CORRECT
payment = Payment(note="text")
```

### Mistake 2: Reading payment.notes attribute
```python
# ❌ WRONG
text = payment.notes

# ✅ CORRECT
text = payment.note
```

### Mistake 3: Confusing with Notice class
```python
# Payment uses 'note' (singular)
payment = Payment(note="payment note")

# Notice uses 'notes' (plural) - different class!
notice = Notice(notes="notice notes")
```

## Remember

**Payment uses `note` (SINGULAR)**
- `payment.note` ✅
- `payment.notes` ❌

**If you see `notes`, it's probably Notice or StorageContract, not Payment!**
