from backend.models.retirement_plan import RetirementPlanInput, TaxCalculationMode
from backend.services.retirement_calculator import RetirementCalculator

# Tighter scenario - money MIGHT run out
base_input = {
    "current_age": 60,
    "retirement_age": 65,
    "life_expectancy": 90,
    "province": "Ontario",
    "rrsp_balance": 250000,
    "tfsa_balance": 100000,
    "non_registered": 0,
    "monthly_contribution": 0,
    "expected_return": 0.05,
    "expected_inflation": 0.025,
    "desired_annual_spending": 52000,  # Aggressive
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

print("Bankruptcy Avoidance Test")
print("="*60)
print(f"SIMPLIFIED Mode:")
print(f"  Final Balance: ${result_simp.final_balance:,.0f}")
print(f"  Success: {result_simp.success}")
print(f"  Warnings: {len(result_simp.warnings)}")

print(f"\nACCURATE Mode:")
print(f"  Final Balance: ${result_acc.final_balance:,.0f}")
print(f"  Success: {result_acc.success}")
print(f"  Warnings: {len(result_acc.warnings)}")

# Check when balances hit zero
print("\nWhen do accounts deplete?")
for age in range(70, 91, 5):
    simp_year = next((y for y in result_simp.projections if y.age == age), None)
    acc_year = next((y for y in result_acc.projections if y.age == age), None)
    
    if simp_year and acc_year:
        print(f"Age {age}: SIMP ${simp_year.total_balance:>9,.0f} | ACC ${acc_year.total_balance:>9,.0f}")
