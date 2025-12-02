# Known Issues

## ~~Tax Calculation Integration Bug~~ ✅ RESOLVED

**Status:** FIXED as of commit `0474f3b`

**Original Issue:** Tax calculations were correct, but withdrawal logic didn't account for tax liabilities, causing SIMPLIFIED and ACCURATE modes to yield identical final balances.

**Root Causes:** 
1. Mandatory RRIF withdrawals were subtracted from balance twice (lines 166 and 271)
2. Additional RRSP withdrawals weren't included in taxable income calculation (line 233)

**Fix Applied:**
- Subtract mandatory RRIF withdrawal once at calculation time (line 166)
- Remove duplicate subtraction (deleted old line 271)
- Include additional RRSP withdrawals in taxable income (line 233: `taxable_income = gross_income + rrsp_additional_withdrawal`)
- Add overdraft protection to prevent negative balances

**Impact:**
- ACCURATE mode now shows ~$29k advantage at age 70
- Benefit persists: ~$2-3k more throughout retirement (ages 75-90)
- Final balance: ~$2,194 more with ACCURATE mode at age 90

**Verification:** See `backend/tests/scratch/test_tax_timeline.py` for before/after comparison.

---

**No other known issues at this time.**
