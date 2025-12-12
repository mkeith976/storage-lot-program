# Storage Days Breakdown - Usage Guide

## Overview

The `balance()` function has been extended to provide detailed analysis of storage days collectibility based on lien timing rules. This helps identify potential collection risks when lien notices are sent late or not sent.

## API Reference

### `balance(contract, as_of=None, include_breakdown=False)`

**Parameters:**
- `contract`: StorageContract instance
- `as_of`: datetime (default: today) - Calculate balance as of this date
- `include_breakdown`: bool (default: False) - Return detailed breakdown

**Returns:**
- If `include_breakdown=False`: `float` - Balance amount only
- If `include_breakdown=True`: `dict` with:
  - `balance`: float - Outstanding balance amount
  - `breakdown`: dict - Storage days analysis (see below)

### `storage_days_breakdown(contract, as_of=None)`

Direct access to breakdown analysis without balance calculation.

**Returns dict with:**
- `total_days`: int - Total storage days charged
- `billable_days`: int - Days clearly collectible under lien rules
- `questionable_days`: int - Days that may not be collectible
- `warning`: str - Warning message if collectibility risk exists (empty if no risk)
- `details`: str - Human-readable explanation

## Collectibility Rules

### Tow & Recovery Contracts (Florida 713.78)

**Timeline affects collectibility:**

1. **Notice sent within 7 days** → All storage days billable
2. **Notice sent late (day 8+)** → Days after deadline may be questionable
3. **No notice sent, past deadline** → Days after deadline at risk

**Calculation Logic:**
- Notice sent on day 12 (5 days late) → 5 questionable days
- No notice sent, currently day 20 → 13 questionable days (20 - 7)

### Storage Only Contracts

**No timing restrictions** - All storage days billable regardless of notice timing.

## GUI Integration Examples

### Example 1: Display Warning in Contract Details

```python
# In lot_gui.py, when displaying contract details:
def display_contract_with_warnings(self, contract):
    # Get balance with breakdown
    result = balance(contract, include_breakdown=True)
    bal = result['balance']
    breakdown = result['breakdown']
    
    # Display balance
    self.balance_label.setText(f"Balance: ${bal:.2f}")
    
    # Show warning if collectibility risk exists
    if breakdown['warning']:
        self.warning_label.setStyleSheet("color: red; font-weight: bold;")
        self.warning_label.setText(breakdown['warning'])
        self.warning_label.setVisible(True)
    else:
        self.warning_label.setVisible(False)
    
    # Show breakdown details
    self.days_breakdown_label.setText(
        f"Storage Days: {breakdown['total_days']} total "
        f"({breakdown['billable_days']} billable, {breakdown['questionable_days']} questionable)"
    )
```

### Example 2: Highlight Risky Contracts in Table

```python
# In lot_gui.py, when populating contract list:
def populate_contract_row(self, row_index, contract):
    # ... existing code ...
    
    # Check for collectibility risk
    breakdown = storage_days_breakdown(contract)
    
    # Color-code balance column based on risk
    if breakdown['questionable_days'] > 0:
        # Yellow/orange for collectibility risk
        balance_item.setBackground(QColor(255, 200, 100))
        balance_item.setToolTip(breakdown['warning'])
    elif bal > 0:
        # Red for past due
        balance_item.setBackground(QColor(255, 100, 100))
```

### Example 3: Export Report with Breakdown

```python
# Generate report with collectibility analysis:
def generate_collectibility_report(contracts):
    report_lines = ["STORAGE COLLECTIBILITY REPORT", "=" * 80, ""]
    
    for contract in contracts:
        result = balance(contract, include_breakdown=True)
        breakdown = result['breakdown']
        
        if breakdown['questionable_days'] > 0:
            report_lines.append(f"Contract #{contract.contract_id} - {contract.customer.name}")
            report_lines.append(f"  Balance: ${result['balance']:.2f}")
            report_lines.append(f"  {breakdown['details']}")
            report_lines.append(f"  ⚠️ {breakdown['warning']}")
            report_lines.append("")
    
    return "\n".join(report_lines)
```

### Example 4: Dashboard Summary

```python
# Calculate collectibility risk across all contracts:
def calculate_portfolio_risk(contracts):
    total_at_risk = 0.0
    risky_contracts = 0
    
    for contract in contracts:
        breakdown = storage_days_breakdown(contract)
        
        if breakdown['questionable_days'] > 0:
            risky_contracts += 1
            # Estimate at-risk amount
            at_risk_amount = breakdown['questionable_days'] * contract.daily_rate
            total_at_risk += at_risk_amount
    
    return {
        'risky_contracts': risky_contracts,
        'estimated_at_risk': total_at_risk
    }
```

## Test Results

From `test_breakdown.py`:

```
TEST 3: Notice sent late (day 12)
Notice Sent: Day 12 (5 days late)
Total Days: 21
Billable Days: 16
Questionable Days: 5
Warning: ⚠️ COLLECTIBILITY RISK: Lien notice sent 5 days late. Storage charges for 5 days 
         (after 7-day deadline) may not be legally collectible from vehicle owner under 
         Florida 713.78.

TEST 4: No notice sent, past 7-day deadline
Days Since Start: 20
Total Days: 21
Billable Days: 7
Questionable Days: 13
Warning: ⚠️ COLLECTIBILITY RISK: Lien notice not sent (overdue by 13 days). Storage charges 
         for 13 days (after 7-day deadline) may not be legally collectible from vehicle owner 
         under Florida 713.78.
```

## Best Practices

1. **Display warnings prominently** - Use red text, icons, or highlighting
2. **Show breakdown in tooltips** - Hover over balance to see details
3. **Generate reports** - Identify at-risk contracts for management review
4. **Track trends** - Monitor how many contracts have collectibility issues
5. **Legal compliance** - Use breakdown data when consulting with attorneys

## Backward Compatibility

The `balance()` function maintains backward compatibility:

```python
# Old usage still works (returns float):
bal = balance(contract)  # Returns: 735.00

# New usage with breakdown (returns dict):
result = balance(contract, include_breakdown=True)
# Returns: {'balance': 735.00, 'breakdown': {...}}
```

## Related Functions

- `lien_eligibility(contract, as_of)` - Check if lien is eligible
- `lien_timeline(contract)` - Get full lien/sale timeline with warnings
- `past_due_status(contract, as_of)` - Check if payment past due
- `storage_days(contract, as_of)` - Calculate total storage days
