from backend.models.retirement_plan import RetirementPlanInput, TaxCalculationMode
from backend.services.retirement_calculator import RetirementCalculator

base_input = {
    "current_age": 60,
    "retirement_age": 65,
    "life_expectancy": 90,
    "province": "Ontario",
    "rrsp_balance": 200000,
    "tfsa_balance": 100000,
    "non_registered": 0,
    "monthly_contribution": 0,
    "expected_return": 0.06,
    "expected_inflation": 0.025,
    "desired_annual_spending": 45000,
    "cpp_start_age": 65,
    "cpp_monthly": 1200,
    "oas_start_age": 65,
    "has_spouse": False
}

accurate_input = RetirementPlanInput(**base_input, tax_calculation_mode=TaxCalculationMode.ACCURATE)
calculator = RetirementCalculator()
result_acc = calculator.calculate_plan(accurate_input)

print("Withdrawal Breakdown - Age 70 Deep Dive")
print("="*80)

year70 = next((y for y in result_acc.projections if y.age == 70), None)
if year70:
    print(f"\nAge 70 Financial Summary:")
    print(f"  RRIF Withdrawal (mandatory): ${year70.rrif_withdrawal:,.0f}")
    print(f"  CPP Income:                  ${year70.cpp_income:,.0f}")
    print(f"  OAS Income:                  ${year70.oas_income:,.0f}")
    print(f"  Gross Income (total):        ${year70.gross_income:,.0f}")
    print(f"  Other Withdrawals:           ${year70.other_withdrawals:,.0f}")
    print(f"  Taxes:                       ${year70.taxes_estimated:,.0f}")
    print(f"  Net Income:                  ${year70.net_income:,.0f}")
    print(f"  Spending:                    ${year70.spending:,.0f}")
    print(f"\n  Balance Check:")
    print(f"  Net Income - Spending = ${year70.net_income - year70.spending:,.0f}")
    
    print(f"\n  What's in 'Other Withdrawals' ($28,731)?")
    print(f"  - Additional RRSP beyond mandatory minimum")
    print(f"  - Used to cover spending + taxes")
    print(f"\n  Total Taxable Income: ${year70.gross_income + year70.other_withdrawals:,.0f}")
    print(f"  (This is what the ${year70.taxes_estimated:,.0f} tax is calculated on)")

