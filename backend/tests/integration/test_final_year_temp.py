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

print("Final Year (Age 90) Comparison:")
print(f"Simplified final: ${result_simp.final_balance:,.2f}")
print(f"Accurate final:   ${result_acc.final_balance:,.2f}")
print(f"Difference:       ${result_acc.final_balance - result_simp.final_balance:,.2f}")

# Check a mid-retirement year
age_75_simp = next((y for y in result_simp.projections if y.age == 75), None)
age_75_acc = next((y for y in result_acc.projections if y.age == 75), None)

if age_75_simp and age_75_acc:
    print(f"\nAge 75 Comparison:")
    print(f"Simplified TFSA: ${age_75_simp.tfsa_balance:,.0f}")
    print(f"Accurate TFSA:   ${age_75_acc.tfsa_balance:,.0f}")
    print(f"TFSA Difference: ${age_75_acc.tfsa_balance - age_75_simp.tfsa_balance:,.0f}")
