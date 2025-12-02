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

simplified_input = RetirementPlanInput(**base_input, tax_calculation_mode=TaxCalculationMode.SIMPLIFIED)
accurate_input = RetirementPlanInput(**base_input, tax_calculation_mode=TaxCalculationMode.ACCURATE)

calculator = RetirementCalculator()
result_simp = calculator.calculate_plan(simplified_input)
result_acc = calculator.calculate_plan(accurate_input)

print("Year-by-Year Tax Comparison (First 5 retirement years)")
print("="*80)
print(f"{'Age':<5} {'Gross Income':>15} {'SIMP Tax':>12} {'ACC Tax':>12} {'Tax Saved':>12} {'TFSA Diff':>12}")
print("-"*80)

for age in range(65, 70):
    simp_year = next((y for y in result_simp.projections if y.age == age), None)
    acc_year = next((y for y in result_acc.projections if y.age == age), None)
    
    if simp_year and acc_year:
        tax_saved = simp_year.taxes_estimated - acc_year.taxes_estimated
        tfsa_diff = acc_year.tfsa_balance - simp_year.tfsa_balance
        print(f"{age:<5} ${simp_year.gross_income:>13,.0f} ${simp_year.taxes_estimated:>10,.0f} ${acc_year.taxes_estimated:>10,.0f} ${tax_saved:>10,.0f} ${tfsa_diff:>10,.0f}")

print(f"\nFinal Balances:")
print(f"SIMPLIFIED: ${result_simp.final_balance:,.0f}")
print(f"ACCURATE:   ${result_acc.final_balance:,.0f}")
print(f"Difference: ${result_acc.final_balance - result_simp.final_balance:,.0f}")
