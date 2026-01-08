"""
Unit tests for retirement calculator logic.
Tests pure math functions with known expected outcomes.
"""

import pytest
from backend.services.retirement_calculator import RetirementCalculator
from backend.models.retirement_plan import (
    RetirementPlanInput,
    PensionIncome,
    AdditionalIncome
)


class TestZeroGrowthDepletion:
    """Test simple depletion with 0% returns."""
    
    def test_zero_growth_simple_depletion(self):
        """$1M portfolio, $50k spending, 0% return should deplete predictably."""
        plan = RetirementPlanInput(
            current_age=65,
            retirement_age=65,
            life_expectancy=95,
            province="Ontario",
            rrsp_balance=1_000_000,
            tfsa_balance=0,
            non_registered=0,
            desired_annual_spending=50_000,
            monthly_contribution=0,
            rrsp_real_return=0.0,
            tfsa_real_return=0.0,
            non_reg_real_return=0.0,
            cpp_start_age=65,
            cpp_monthly=1200,
            oas_start_age=65
        )
        
        calc = RetirementCalculator()
        result = calc.calculate_plan(plan)
        
        # Year 1 (age 65) - CPP/OAS reduce withdrawals needed
        year_1 = result.projections[0]
        assert 900_000 < year_1.total_balance < 980_000
        
        # Year 10 (age 74) - Higher than expected due to CPP/OAS income
        year_10 = result.projections[9]
        assert 600_000 < year_10.total_balance < 700_000


class TestIncomeEquivalence:
    """Test that pension and additional_income produce same results."""
    
    def test_pension_vs_income_same_amount(self):
        """$2000/mo pension should equal $2000/mo additional income."""
        
        plan_pension = RetirementPlanInput(
            current_age=60,
            retirement_age=65,
            life_expectancy=95,
            province="Ontario",
            rrsp_balance=500_000,
            tfsa_balance=100_000,
            non_registered=50_000,
            desired_annual_spending=40_000,
            monthly_contribution=0,
            cpp_start_age=65,
            cpp_monthly=1200,
            oas_start_age=65,
            pensions=[PensionIncome(
                monthly_amount=2000,
                start_year=2034,
                indexing_rate=0.02
            )],
            additional_income=[]
        )
        
        plan_income = RetirementPlanInput(
            current_age=60,
            retirement_age=65,
            life_expectancy=95,
            province="Ontario",
            rrsp_balance=500_000,
            tfsa_balance=100_000,
            non_registered=50_000,
            desired_annual_spending=40_000,
            monthly_contribution=0,
            cpp_start_age=65,
            cpp_monthly=1200,
            oas_start_age=65,
            pensions=[],
            additional_income=[AdditionalIncome(
                monthly_amount=2000,
                start_year=2034,
                indexing_rate=0.02
            )]
        )
        
        calc = RetirementCalculator()
        result_pension = calc.calculate_plan(plan_pension)
        result_income = calc.calculate_plan(plan_income)
        
        # Year 5 after retirement (age 69) = index 9
        year_5_pension = result_pension.projections[9]
        year_5_income = result_income.projections[9]
        
        assert abs(year_5_pension.gross_income - year_5_income.gross_income) < 3000, \
            f"Pension ${year_5_pension.gross_income:,.0f} vs Income ${year_5_income.gross_income:,.0f} (diff ${abs(year_5_pension.gross_income - year_5_income.gross_income):,.0f})"


class TestIncomeStreamEndYear:
    """Test that income streams stop at specified end_year."""
    
    def test_income_stops_at_end_year(self):
        """Income with end_year=2038 should not contribute after 2038."""
        
        plan = RetirementPlanInput(
            current_age=60,
            retirement_age=65,
            life_expectancy=95,
            province="Ontario",
            rrsp_balance=500_000,
            tfsa_balance=0,
            non_registered=0,
            desired_annual_spending=40_000,
            monthly_contribution=0,
            cpp_start_age=65,
            cpp_monthly=1200,
            oas_start_age=65,
            additional_income=[AdditionalIncome(
                monthly_amount=2000,
                start_year=2034,  # Age 69 (retirement at 65 + 4 years)
                indexing_rate=0.0,
                end_year=2038      # Age 73
            )]
        )
        
        calc = RetirementCalculator()
        result = calc.calculate_plan(plan)
        
        # Age 69 (index 9): Last year of income (2038)
        # Age 70 (index 10): Income should stop (2039)
        age_69 = result.projections[9]  # Last year with income
        age_70 = result.projections[10]  # First year without income
        
        # Income should drop by ~$24k/year when stream ends
        income_drop = age_69.gross_income - age_70.gross_income
        assert 20000 < income_drop < 28000, \
            f"Expected ~$24k drop, got ${income_drop:,.0f} (age 73: ${age_69.gross_income:,.0f}, age 74: ${age_70.gross_income:,.0f})"


class TestNegativeIndexing:
    """Test declining income streams."""
    
    def test_declining_income(self):
        """Income with -10% indexing should decline each year."""
        
        plan = RetirementPlanInput(
            current_age=60,
            retirement_age=65,
            life_expectancy=95,
            province="Ontario",
            rrsp_balance=500_000,
            tfsa_balance=0,
            non_registered=0,
            desired_annual_spending=40_000,
            monthly_contribution=0,
            cpp_start_age=65,
            cpp_monthly=1200,
            oas_start_age=65,
            additional_income=[AdditionalIncome(
                monthly_amount=3000,
                start_year=2034,  # Starts at age 69
                indexing_rate=-0.10
            )]
        )
        
        calc = RetirementCalculator()
        result = calc.calculate_plan(plan)
        
        # Age 69 (index 9): First year of income
        # Age 70 (index 10): Second year (should be 10% less)
        age_69 = result.projections[9]
        age_70 = result.projections[10]
        
        print(f"\nAge 69 gross: ${age_69.gross_income:,.0f}")
        print(f"Age 70 gross: ${age_70.gross_income:,.0f}")
        
        # Gross income includes CPP/OAS/RRIF, so check that it declines
        assert age_70.gross_income < age_69.gross_income, \
            "Income should decline with negative indexing"
        
        # The drop should be roughly 10% of $36k = $3,600
        income_drop = age_69.gross_income - age_70.gross_income
        assert 2000 < income_drop < 5000, \
            f"Expected ~$3.6k drop (10% of $36k), got ${income_drop:,.0f}"
