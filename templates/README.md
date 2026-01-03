# Analysis Templates for Batch Results

## Available Templates

### 1. Excel Template
**File:** `Retirement_Analysis_Template.xlsx`

**Features:**
- Summary dashboard with key metrics
- Top 10 scenarios auto-ranked
- Scenario comparison tool
- Pre-formatted charts
- Filter helpers

**How to Use:**
1. Download your batch CSV results
2. Open `Retirement_Analysis_Template.xlsx`
3. Paste CSV data into "Raw Data" sheet (starting at A2)
4. All other sheets auto-update

---

### 2. Google Sheets Template
**File:** `GOOGLE_SHEETS_GUIDE.md`

**Features:**
- Same analysis as Excel version
- Cloud-based, shareable
- Mobile-friendly
- Auto-save

**How to Use:**
1. Read `GOOGLE_SHEETS_GUIDE.md` for setup instructions
2. Copy the template (link in guide)
3. Import your CSV file
4. Analysis auto-updates

---

## What's Included in Analysis

### Summary Metrics
- Total scenarios calculated
- Success rate (% viable plans)
- Failed scenarios count
- Average final balance

### Top Scenarios
- Ranked by final balance
- Shows optimal retirement ages
- Compares starting balances
- Identifies best spending levels

### Scenario Comparison
- Compare up to 5 scenarios side-by-side
- See trade-offs between options
- Understand impact of variables

### Visual Charts
- Balance progression over time
- Success rate by retirement age
- Spending vs outcome analysis

---

## Tips for Analysis

### Finding Your Best Plan
1. Filter for successful scenarios (success = TRUE)
2. Sort by final balance (highest first)
3. Look for lowest retirement age with success
4. Consider your personal preferences

### Understanding Trade-offs
- Earlier retirement = higher initial balance needed
- Higher spending = more risk of failure
- Pensions significantly extend plan viability
- Property sales provide liquidity at specific ages

### When Plans Fail
Check the "warnings" column to see:
- Age when money runs out
- Specific shortfalls
- Contributing factors

---

## Support

Questions? Issues?
- Check API docs: https://web-production-c1f93.up.railway.app/docs
- Test scenarios: https://retirement-planning-dapp.vercel.app

---

*Part of Retirement Planning DApp*
*Canadian tax calculations, batch scenario analysis*
