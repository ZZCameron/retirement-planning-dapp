# Next Session: Fix Tax Withdrawal Logic

## Goal
Make tax calculation mode actually affect final balances by withdrawing enough to cover tax liabilities.

## Current State
- ✅ Tax calculator integrated
- ✅ SIMPLIFIED vs ACCURATE modes work
- ✅ Tax amounts calculated correctly
- ❌ Withdrawals don't account for taxes
- ❌ Final balances are identical

## The Fix (30-45 minutes)

### Step 1: Backup Current Code
```bash
cp backend/services/retirement_calculator.py backend/services/retirement_calculator.py.before_withdrawal_fix
> ^C
(venv) ubuntuforsolana@BuzzBusiness:~/retirement-planning-dapp$ cat > NEXT_SESSION.md << 'EOF'
# Next Session: Fix Tax Withdrawal Logic

## Goal
Make tax calculation mode actually affect final balances by withdrawing enough to cover tax liabilities.

## Current State
- ✅ Tax calculator integrated
- ✅ SIMPLIFIED vs ACCURATE modes work
- ✅ Tax amounts calculated correctly
- ❌ Withdrawals don't account for taxes
- ❌ Final balances are identical

## The Fix (30-45 minutes)

### Step 1: Backup Current Code
```bash
cp backend/services/retirement_calculator.py backend/services/retirement_calculator.py.before_withdrawal_fix
Step 2: Reorder Calculation Logic
In retirement_calculator.py, around lines 196-250:

Current order:

Calculate gross income
Withdraw to cover adjusted_spending
Calculate taxes (too late!)
New order:

Calculate gross income
Estimate taxes first
Calculate total_need = adjusted_spending + taxes
Withdraw to cover total_need
Step 3: Test Scenarios
Expected Results After Fix:

Age 65: ACCURATE mode has ~$4,000 more in TFSA
Age 75: Difference compounds to ~$10,000+
Final balance: ACCURATE mode significantly higher
Step 4: Verify and Commit
Run integration tests:

Copypython3 backend/tests/integration/test_tax_modes_temp.py
python3 backend/tests/integration/test_tax_debug.py
Should see:

Different final balances
ACCURATE mode leaves more money
Tax savings compound over time
Files to Modify
backend/services/retirement_calculator.py (lines 196-250)
Files to Review
backend/KNOWN_ISSUES.md (delete after fix)
backend/tests/integration/*_temp.py (convert to proper pytest)
Success Criteria
 ACCURATE mode has higher final balance than SIMPLIFIED
 Tax savings visible in year-by-year projections
 TFSA balance diverges between modes
 Integration tests pass with different results
 Code committed with "Fix tax withdrawal logic" message
Estimated Time
30-45 minutes

Backup Plan
If stuck after 1 hour, create feature/fix-tax-withdrawal-v2 branch and ask for help.    
