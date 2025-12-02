from backend.models.retirement_plan import RetirementPlanInput, TaxCalculationMode
from backend.services.retirement_calculator import RetirementCalculator

base_input = {
    "current_age": 35,
    "retirement_age": 65,
    "life_expectancy": 90,
    "province": "Ontario",
    "rrsp_balance": 100000,
    "tfsa_balance": 50000,
    "non_registered": 0,
    "monthly_contribution": 1000,
    "expected_return": 0.06,
    "expected_inflation": 0.02,
    "desired_annual_spending": 60000,
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

print("Balance Comparison Over Time:")
print("="*70)
print(f"{'Age':<5} {'SIMPLIFIED':>20} {'ACCURATE':>20} {'Difference':>15}")
print("-"*70)

for age in [65, 68, 70, 72, 75, 80, 85, 90]:
    simp_year = next((y for y in result_simp.projections if y.age == age), None)
    acc_year = next((y for y in result_acc.projections if y.age == age), None)
    
    if simp_year and acc_year:
        diff = acc_year.total_balance - simp_year.total_balance
        print(f"{age:<5} ${simp_year.total_balance:>18,.0f} ${acc_year.total_balance:>18,.0f} ${diff:>13,.0f}")
        
        # Show which accounts differ
        if abs(diff) > 100:
            tfsa_diff = acc_year.tfsa_balance - simp_year.tfsa_balance
            rrsp_diff = acc_year.rrsp_rrif_balance - simp_year.rrsp_rrif_balance
            print(f"      └─ TFSA: ${tfsa_diff:+,.0f} | RRSP: ${rrsp_diff:+,.0f}")

print("\nFinal Result:")
print(f"SIMPLIFIED: ${result_simp.final_balance:,.0f}")
print(f"ACCURATE:   ${result_acc.final_balance:,.0f}")
print(f"Difference: ${result_acc.final_balance - result_simp.final_balance:,.0f}")
