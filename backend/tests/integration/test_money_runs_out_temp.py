from backend.models.retirement_plan import RetirementPlanInput, TaxCalculationMode
from backend.services.retirement_calculator import RetirementCalculator

# Tighter scenario - money will run low
base_input = {
    "current_age": 60,
    "retirement_age": 65,
    "life_expectancy": 90,
    "province": "Ontario",
    "rrsp_balance": 200000,
    "tfsa_balance": 100000,
    "non_registered": 0,
    "monthly_contribution": 0,
    "expected_return": 0.05,
    "expected_inflation": 0.025,
    "desired_annual_spending": 50000,  # Aggressive spending
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

print("Scenario: Aggressive spending, moderate savings")
print("="*60)
print(f"\nSIMPLIFIED (25% tax):")
print(f"  Final Balance: ${result_simp.final_balance:,.0f}")
print(f"  Plan Success: {result_simp.success}")
print(f"  Warnings: {len(result_simp.warnings)}")

print(f"\nACCURATE (Provincial tax):")
print(f"  Final Balance: ${result_acc.final_balance:,.0f}")
print(f"  Plan Success: {result_acc.success}")
print(f"  Warnings: {len(result_acc.warnings)}")

# Find when money runs low
print("\n" + "="*60)
print("When do accounts hit critical levels?")
print("="*60)

for age in [70, 75, 80, 85, 90]:
    simp_year = next((y for y in result_simp.projections if y.age == age), None)
    acc_year = next((y for y in result_acc.projections if y.age == age), None)
    
    if simp_year and acc_year:
        print(f"\nAge {age}:")
        print(f"  SIMPLIFIED: RRSP ${simp_year.rrsp_rrif_balance:>8,.0f} | TFSA ${simp_year.tfsa_balance:>8,.0f} | Total ${simp_year.total_balance:>9,.0f}")
        print(f"  ACCURATE:   RRSP ${acc_year.rrsp_rrif_balance:>8,.0f} | TFSA ${acc_year.tfsa_balance:>8,.0f} | Total ${acc_year.total_balance:>9,.0f}")
        diff = acc_year.total_balance - simp_year.total_balance
        print(f"  Difference: ${diff:+,.0f} ({'Accurate better' if diff > 0 else 'Same' if diff == 0 else 'Simplified better'})")
