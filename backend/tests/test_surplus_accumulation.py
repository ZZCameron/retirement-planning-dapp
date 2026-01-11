"""
Test: Verify surplus income accumulates in non-registered account
"""
from backend.services.retirement_calculator import RetirementCalculator
from backend.models.retirement_plan import RetirementPlanInput, AdditionalIncome

def test_surplus_grows_accounts():
    """Test that 10% income growth causes accounts to GROW, not deplete"""
    
    plan = RetirementPlanInput(
        current_age=64,
        retirement_age=65,
        life_expectancy=95,
        province="Ontario",
        rrsp_balance=420000,
        tfsa_balance=160000,
        non_registered=2000000,
        desired_annual_spending=120000,
        monthly_contribution=0,
        rrsp_real_return=0.02,
        tfsa_real_return=0.02,
        non_reg_real_return=0.02,
        cpp_start_age=65,
        cpp_monthly=1200,
        oas_start_age=65,
        pensions=[],
        additional_income=[
            AdditionalIncome(
                monthly_amount=1000,
                start_year=2025,
                indexing_rate=0.10,  # 10% growth
                end_year=None
            )
        ],
        real_estate_holdings=[]
    )
    
    calc = RetirementCalculator()
    result = calc.calculate_plan(plan)
    
    print("\n" + "="*70)
    print("🧪 TEST: Surplus Accumulation with 10% Income Growth")
    print("="*70)
    
    # Check key years
    ages_to_check = [65, 70, 75, 80, 85, 90]
    
    for age in ages_to_check:
        idx = age - 64
        if idx < len(result.projections):
            proj = result.projections[idx]
            total = proj.rrsp_rrif_balance + proj.tfsa_balance + proj.non_registered_balance
            
            print(f"\nAge {age}:")
            print(f"  Total Balance: ${total:>12,.0f}")
            print(f"  Gross Income:  ${proj.gross_income:>12,.0f}")
            print(f"  Non-Reg:       ${proj.non_registered_balance:>12,.0f}")
    
    # Key assertion: Total balance at age 85 should be HIGHER than age 65
    age_65_total = result.projections[1].total_balance
    age_85_total = result.projections[21].total_balance
    
    print("\n" + "="*70)
    print(f"Age 65 total: ${age_65_total:,.0f}")
    print(f"Age 85 total: ${age_85_total:,.0f}")
    
    if age_85_total > age_65_total:
        print("✅ PASS: Accounts grew due to surplus income accumulation!")
    else:
        print(f"❌ FAIL: Accounts should grow, but age 85 < age 65")
        print(f"   Difference: ${age_85_total - age_65_total:,.0f}")
    
    print("="*70 + "\n")
    
    assert age_85_total > age_65_total, "Accounts should grow with 10% income indexing"

if __name__ == "__main__":
    test_surplus_grows_accounts()
    print("✅ Test passed!")
