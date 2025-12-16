#!/usr/bin/env python3
"""Test script to verify Payment note/notes field consistency.

This verifies:
1. Payment objects can be created with 'note' field
2. JSON with old 'notes' field loads correctly (backward compatibility)
3. JSON with new 'note' field loads correctly
4. Payment notes are preserved through save/load cycle
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime

# Add parent dir to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from lot_models import Payment, Customer, Vehicle, StorageContract, StorageData, DATE_FORMAT
from persistence import load_data, save_data


def test_payment_creation():
    """Test creating Payment with 'note' field."""
    print("Test 1: Creating Payment with 'note' field...")
    payment = Payment(
        date="2025-12-12",
        amount=100.0,
        method="cash",
        note="Test payment note"
    )
    assert payment.note == "Test payment note", "Payment note not set correctly"
    print("✓ Payment created successfully with note field")
    return payment


def test_payment_to_dict():
    """Test Payment serialization to dict."""
    print("\nTest 2: Payment serialization to dict...")
    payment = Payment(
        date="2025-12-12",
        amount=100.0,
        method="cash",
        note="Test note"
    )
    data = payment.to_dict()
    assert "note" in data, "Payment.to_dict() missing 'note' field"
    assert data["note"] == "Test note", "Payment.to_dict() note value incorrect"
    print(f"✓ Serialized payment dict: {data}")
    return data


def test_payment_from_dict_with_note():
    """Test Payment deserialization from dict with 'note' field."""
    print("\nTest 3: Payment deserialization from dict with 'note' field...")
    data = {
        "date": "2025-12-12",
        "amount": 100.0,
        "method": "cash",
        "note": "Current format note"
    }
    payment = Payment.from_dict(data)
    assert payment.note == "Current format note", "Payment.from_dict() with 'note' failed"
    print("✓ Payment loaded from dict with 'note' field")
    return payment


def test_payment_from_dict_with_notes_legacy():
    """Test Payment deserialization from dict with 'notes' field (legacy)."""
    print("\nTest 4: Payment deserialization from dict with 'notes' field (LEGACY)...")
    data = {
        "date": "2025-12-12",
        "amount": 150.0,
        "method": "card",
        "notes": "Legacy format notes"  # Old field name
    }
    payment = Payment.from_dict(data)
    assert payment.note == "Legacy format notes", "Payment.from_dict() backward compatibility with 'notes' failed"
    print("✓ Payment loaded from dict with 'notes' field (backward compatible)")
    return payment


def test_full_save_load_cycle():
    """Test full save/load cycle with payments."""
    print("\nTest 5: Full save/load cycle with payments...")
    
    # Create test contract with payments
    customer = Customer(name="Test Customer", phone="555-1234", address="123 Test St")
    vehicle = Vehicle(vehicle_type="Car", make="Honda", model="Civic", year=2020, 
                     plate="ABC123", vin="1HGBH41JXMN109186", color="Blue")
    
    contract = StorageContract(
        contract_id=1,
        customer=customer,
        vehicle=vehicle,
        start_date=datetime.today().strftime(DATE_FORMAT),
        contract_type="Storage",
        daily_storage_fee=35.0,
        admin_fee=75.0,
    )
    
    # Add payments with notes
    payment1 = Payment(date="2025-12-12", amount=100.0, method="cash", note="Initial payment")
    payment2 = Payment(date="2025-12-13", amount=50.0, method="card", note="Second payment")
    contract.payments = [payment1, payment2]
    
    storage_data = StorageData(next_id=2, contracts=[contract])
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        save_data(storage_data, temp_path)
        print(f"  ✓ Saved to {temp_path}")
        
        # Load back
        loaded_data = load_data(temp_path)
        print(f"  ✓ Loaded from {temp_path}")
        
        # Verify
        assert len(loaded_data.contracts) == 1, "Contract count mismatch"
        loaded_contract = loaded_data.contracts[0]
        assert len(loaded_contract.payments) == 2, "Payment count mismatch"
        
        # Check payment notes
        p1 = loaded_contract.payments[0]
        p2 = loaded_contract.payments[1]
        assert p1.note == "Initial payment", f"Payment 1 note mismatch: got '{p1.note}'"
        assert p2.note == "Second payment", f"Payment 2 note mismatch: got '{p2.note}'"
        
        print(f"  ✓ Payment 1 note: '{p1.note}'")
        print(f"  ✓ Payment 2 note: '{p2.note}'")
        print("✓ Save/load cycle preserved payment notes")
        
    finally:
        # Cleanup
        temp_path.unlink()


def test_json_with_legacy_notes_field():
    """Test loading JSON file with legacy 'notes' field."""
    print("\nTest 6: Loading JSON with legacy 'notes' field...")
    
    # Create JSON with old 'notes' field
    legacy_json = {
        "next_id": 2,
        "contracts": [{
            "contract_id": 1,
            "customer": {
                "name": "Legacy Customer",
                "phone": "555-9999",
                "address": "Old St"
            },
            "vehicle": {
                "vehicle_type": "Car",
                "make": "Toyota",
                "model": "Camry",
                "year": 2019,
                "plate": "OLD123",
                "vin": "1HGBH41JXMN109999",
                "color": "Red"
            },
            "start_date": "2025-01-01",
            "contract_type": "Storage",
            "rate_mode": "daily",
            "daily_storage_fee": 35.0,
            "weekly_storage_fee": 210.0,
            "monthly_storage_fee": 840.0,
            "admin_fee": 75.0,
            "status": "Active",
            "payments": [
                {
                    "date": "2025-01-15",
                    "amount": 200.0,
                    "method": "cash",
                    "notes": "Legacy payment with 'notes' field"  # OLD FIELD NAME
                }
            ],
            "notices": [],
            "notes": [],
            "attachments": []
        }]
    }
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(legacy_json, f, indent=2)
        temp_path = Path(f.name)
    
    try:
        # Load the legacy format
        loaded_data = load_data(temp_path)
        print(f"  ✓ Loaded legacy JSON from {temp_path}")
        
        # Verify payment note was migrated
        contract = loaded_data.contracts[0]
        payment = contract.payments[0]
        assert payment.note == "Legacy payment with 'notes' field", \
            f"Legacy 'notes' field not migrated to 'note': got '{payment.note}'"
        
        print(f"  ✓ Migrated payment note: '{payment.note}'")
        print("✓ Backward compatibility works: legacy 'notes' → 'note'")
        
    finally:
        temp_path.unlink()


def main():
    """Run all tests."""
    print("="*60)
    print("Payment Field Consistency Tests")
    print("="*60)
    
    try:
        test_payment_creation()
        test_payment_to_dict()
        test_payment_from_dict_with_note()
        test_payment_from_dict_with_notes_legacy()
        test_full_save_load_cycle()
        test_json_with_legacy_notes_field()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nSummary:")
        print("  ✓ Payment uses 'note' field (singular)")
        print("  ✓ Payment.to_dict() includes 'note'")
        print("  ✓ Payment.from_dict() handles 'note'")
        print("  ✓ Payment.from_dict() handles legacy 'notes' (backward compatible)")
        print("  ✓ Save/load cycle preserves payment notes")
        print("  ✓ Legacy JSON files load correctly")
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
