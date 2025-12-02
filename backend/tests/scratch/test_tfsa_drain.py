from backend.models.retirement_plan import RetirementPlanInput, TaxCalculationMode
from backend.services.retirement_calculator import RetirementCalculator

base_input = {
    "current_age": 63,
    "retirement_age": 65,
    "life_expectancy": 75,
    "province": "Ontario",
    "rrsp_balance": 200000,
    "tfsa_balance": 100000,
    "non_registered": 0,
    "monthly_contribution": 0,
    "expected_return": 0.05,
    "expected_inflation": 0.02,
    "desired_annual_spending": 45000,
    "cpp_start_age": 65,
    "cpp_monthly": 1200,
    "oas_start_age": 65,
    "has_spouse": False
}

accurate_input = RetirementPlanInput(**base_input, tax_calculation_mode=TaxCalculationMode.ACCURATE)
calculator = RetirementCalculator()
result_acc = calculator.calculate_plan(accurate_input)

print("ACCURATE Mode - Detailed Account Tracking")
print("="*100)
print(f"{'Age':<5} {'RRSP Start':>12} {'RRIF Wdraw':>12} {'Other Wdraw':>12} {'Taxes':>10} {'TFSA End':>12} {'RRSP End':>12}")
print("-"*100)

for age in range(65, 75):
    year = next((y for y in result_acc.projections if y.age == age), None)
    if year:
        # Calculate RRSP at start of year (before withdrawal but after previous year's growth)
        if age > 65:
            prev_year = next((y for y in result_acc.projections if y.age == age-1), None)
            rrsp_start = prev_year.rrsp_rrif_balance if prev_year else 0
        else:
            rrsp_start = 200000  # Initial
        
        print(f"{age:<5} ${rrsp_start:>10,.0f} ${year.rrif_withdrawal:>10,.0f} ${year.other_withdrawals:>10,.0f} ${year.taxes_estimated:>8,.0f} ${year.tfsa_balance:>10,.0f} ${year.rrsp_rrif_balance:>10,.0f}")

print("\nKey Question: Why does TFSA drop to $0 at age 69?")
print("Look at 'Other Wdraw' column - this is TFSA + Non-Reg withdrawals")
