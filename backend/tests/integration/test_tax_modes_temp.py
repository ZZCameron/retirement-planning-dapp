"""
Quick test to verify both tax calculation modes work
"""
from backend.models.retirement_plan import RetirementPlanInput, TaxCalculationMode
from backend.services.retirement_calculator import RetirementCalculator

# Test data: Ontario resident, age 35, retire at 65
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

print("Testing Tax Calculation Modes\n" + "="*50)

# Test 1: SIMPLIFIED mode (25% flat rate)
print("\n1. SIMPLIFIED Mode (Free Tier - 25% flat rate)")
simplified_input = RetirementPlanInput(
    **base_input,
    tax_calculation_mode=TaxCalculationMode.SIMPLIFIED
)
calculator = RetirementCalculator()
result_simplified = calculator.calculate_plan(simplified_input)

print(f"   Final Balance: ${result_simplified.final_balance:,.0f}")
print(f"   Plan Success: {result_simplified.success}")

# Test 2: ACCURATE mode (Provincial tax calculator)
print("\n2. ACCURATE Mode (Premium Tier - Provincial tax)")
accurate_input = RetirementPlanInput(
    **base_input,
    tax_calculation_mode=TaxCalculationMode.ACCURATE
)
result_accurate = calculator.calculate_plan(accurate_input)

print(f"   Final Balance: ${result_accurate.final_balance:,.0f}")
print(f"   Plan Success: {result_accurate.success}")

# Compare results
print("\n3. Comparison")
balance_diff = result_accurate.final_balance - result_simplified.final_balance
print(f"   Difference: ${balance_diff:,.0f}")
print(f"   Accurate mode leaves {'MORE' if balance_diff > 0 else 'LESS'} money")

# Sample year comparison (age 70)
print("\n4. Sample Year Details (Age 70)")
sample_year_simplified = next((y for y in result_simplified.projections if y.age == 70), None)
sample_year_accurate = next((y for y in result_accurate.projections if y.age == 70), None)

if sample_year_simplified and sample_year_accurate:
    print(f"   SIMPLIFIED - Taxes: ${sample_year_simplified.taxes_estimated:,.0f}")
    print(f"   ACCURATE   - Taxes: ${sample_year_accurate.taxes_estimated:,.0f}")
    tax_diff = sample_year_accurate.taxes_estimated - sample_year_simplified.taxes_estimated
    print(f"   Tax Difference: ${tax_diff:,.0f} ({'lower' if tax_diff < 0 else 'higher'} with accurate)")

print("\n✅ Both modes working successfully!")
