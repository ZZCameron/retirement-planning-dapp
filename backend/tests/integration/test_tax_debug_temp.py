"""
Debug test - trace exactly what's happening with taxes
"""
from backend.models.retirement_plan import RetirementPlanInput, TaxCalculationMode
from backend.services.retirement_calculator import RetirementCalculator

base_input = {
    "current_age": 63,
    "retirement_age": 65,
    "life_expectancy": 75,  # Shorter for easier debugging
    "province": "Ontario",
    "rrsp_balance": 100000,
    "tfsa_balance": 50000,
    "non_registered": 0,
    "monthly_contribution": 0,  # No contributions, already retired
    "expected_return": 0.05,
    "expected_inflation": 0.02,
    "desired_annual_spending": 40000,
    "cpp_start_age": 65,
    "cpp_monthly": 1200,
    "oas_start_age": 65,
    "has_spouse": False
}

print("="*60)
print("SIMPLIFIED MODE (25% flat tax)")
print("="*60)

simplified_input = RetirementPlanInput(
    **base_input,
    tax_calculation_mode=TaxCalculationMode.SIMPLIFIED
)
calculator = RetirementCalculator()
result_simplified = calculator.calculate_plan(simplified_input)

print("\nAge 65 Details:")
age_65_simp = next((y for y in result_simplified.projections if y.age == 65), None)
if age_65_simp:
    print(f"  RRSP Balance:  ${age_65_simp.rrsp_rrif_balance:,.0f}")
    print(f"  TFSA Balance:  ${age_65_simp.tfsa_balance:,.0f}")
    print(f"  Total Balance: ${age_65_simp.total_balance:,.0f}")
    print(f"  RRIF Withdrawal: ${age_65_simp.rrif_withdrawal:,.0f}")
    print(f"  CPP Income:    ${age_65_simp.cpp_income:,.0f}")
    print(f"  OAS Income:    ${age_65_simp.oas_income:,.0f}")
    print(f"  Taxes:         ${age_65_simp.taxes_estimated:,.0f}")

print("\n" + "="*60)
print("ACCURATE MODE (Provincial tax)")
print("="*60)

accurate_input = RetirementPlanInput(
    **base_input,
    tax_calculation_mode=TaxCalculationMode.ACCURATE
)
result_accurate = calculator.calculate_plan(accurate_input)

print("\nAge 65 Details:")
age_65_acc = next((y for y in result_accurate.projections if y.age == 65), None)
if age_65_acc:
    print(f"  RRSP Balance:  ${age_65_acc.rrsp_rrif_balance:,.0f}")
    print(f"  TFSA Balance:  ${age_65_acc.tfsa_balance:,.0f}")
    print(f"  Total Balance: ${age_65_acc.total_balance:,.0f}")
    print(f"  RRIF Withdrawal: ${age_65_acc.rrif_withdrawal:,.0f}")
    print(f"  CPP Income:    ${age_65_acc.cpp_income:,.0f}")
    print(f"  OAS Income:    ${age_65_acc.oas_income:,.0f}")
    print(f"  Taxes:         ${age_65_acc.taxes_estimated:,.0f}")

print("\n" + "="*60)
print("COMPARISON")
print("="*60)
if age_65_simp and age_65_acc:
    print(f"Tax difference: ${age_65_simp.taxes_estimated - age_65_acc.taxes_estimated:,.0f}")
    print(f"RRSP difference: ${age_65_simp.rrsp_rrif_balance - age_65_acc.rrsp_rrif_balance:,.0f}")
    print(f"TFSA difference: ${age_65_simp.tfsa_balance - age_65_acc.tfsa_balance:,.0f}")
    print(f"Total difference: ${age_65_simp.total_balance - age_65_acc.total_balance:,.0f}")
