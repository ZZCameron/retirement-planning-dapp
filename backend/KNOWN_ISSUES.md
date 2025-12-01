# Known Issues

## Tax Calculation Integration (Discovered 2024-11-30)

### Issue
Tax calculations work correctly (SIMPLIFIED vs ACCURATE modes produce different tax amounts), but the withdrawal logic doesn't properly account for tax liabilities, resulting in identical final balances.

### Root Cause
The withdrawal logic (lines ~200-220 in `retirement_calculator.py`) calculates withdrawals to cover `adjusted_spending` BEFORE taxes are calculated. When taxes are then calculated (lines ~226+), the code doesn't withdraw additional funds to cover the tax liability.

### Evidence
- Test at age 65: SIMPLIFIED pays $5,740 tax, ACCURATE pays $1,754 tax
- Expected: ACCURATE mode should have $3,986 more in TFSA
- Actual: Both modes end with identical balances by age 70+

### Impact
- Free tier (SIMPLIFIED) and Premium tier (ACCURATE) produce identical projections
- No financial incentive for users to upgrade
- Tax optimization features are non-functional

### Fix Required
Reorder calculation logic to:
1. Calculate gross income (CPP, OAS, RRIF, pension)
2. Estimate taxes on gross income
3. Calculate total need = adjusted_spending + taxes
4. Withdraw from TFSA/non-registered to cover total need

### Priority
**HIGH** - Blocks freemium monetization strategy

### Assigned To
Next development session

### Related Files
- `backend/services/retirement_calculator.py` (lines 200-250)
- `backend/models/retirement_plan.py` (TaxCalculationMode)
- `backend/models/tax_calculator.py` (working correctly)

### Test Cases
- `test_tax_modes.py` - Integration test showing identical balances
- `test_tax_debug.py` - Debug test showing tax differences at age 65
