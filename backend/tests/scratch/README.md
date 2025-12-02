# Scratch Test Scripts

This directory contains ad-hoc test scripts used during development for debugging and verification. These are **not** part of the automated test suite but are preserved for reference and potential reuse.

## Files

- `test_tax_modes_temp.py` - Compare SIMPLIFIED vs ACCURATE tax calculation modes
- `test_tax_timeline.py` - Track tax differences over retirement timeline (ages 65-90)
- `test_tfsa_drain.py` - Detailed account tracking to debug TFSA depletion
- `test_withdrawal_breakdown.py` - Deep dive into withdrawal component breakdown at specific age
- `test_bankruptcy_avoided.py` - Test financial scenarios near bankruptcy
- `test_tax_detailed.py` - Year-by-year tax comparison (first 5 retirement years)
- `test_money_runs_out.py` - Aggressive spending scenario testing
- `test_final_year.py` - Final balance comparison at life expectancy
- `test_tax_debug_temp.py` - Age 65 detailed debugging output
- `test_tax_modes.py` - Original tax mode comparison test

## Usage

Run from project root:
```bash
python3 backend/tests/scratch/test_tax_timeline.py
These scripts are NOT run by pytest and are for manual debugging only.

Key Insights from Testing
Tax benefit peaks at age 70: ~$29k more with ACCURATE mode
Benefit persists after TFSA depletion: ~$2-3k advantage continues through age 90
Final retirement value: ACCURATE mode leaves ~$2,194 more at life expectancy
Freemium value proposition: "Save $2,000+ over retirement with accurate tax calculations"
