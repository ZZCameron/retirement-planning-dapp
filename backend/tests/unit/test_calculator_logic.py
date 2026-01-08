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
            rrsp_balance=1_000_000,
            tfsa_balance=0,
            non_registered=0,
            desired_annual_spending=50_000,
            monthly_contribution=0,
            rrsp_real_return=0.0,
            tfsa_real_return=0.0,
            non_reg_real_return=0.0,
            cpp_start_age=65,
            oas_start_age=65
        )
        
        calc = RetirementCalculator(plan)
        result = calc.calculate()
        
        year_1 = result.projections[0]
        assert 900_000 < year_1.total_balance < 970_000
        
        year_10 = result.projections[9]
        assert 400_000 < year_10.total_balance < 600_000


class TestIncomeEquivalence:
    """Test that pension and additional_income produce same results."""
    
    def test_pension_vs_income_same_amount(self):
        """$2000/mo pension should equal $2000/mo additional income."""
        
        plan_pension = RetirementPlanInput(
            current_age=60,
            retirement_age=65,
            rrsp_balance=500_000,
            tfsa_balance=100_000,
            non_registered=50_000,
            desired_annual_spending=40_000,
            monthly_contribution=0,
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
            rrsp_balance=500_000,
            tfsa_balance=100_000,
            non_registered=50_000,
            desired_annual_spending=40_000,
            monthly_contribution=0,
            pensions=[],
            additional_income=[AdditionalIncome(
                monthly_amount=2000,
                start_year=2034,
                indexing_rate=0.02
            )]
        )
        
        result_pension = RetirementCalculator(plan_pension).calculate()
        result_income = RetirementCalculator(plan_income).calculate()
        
        year_5_pension = result_pension.projections[4]
        year_5_income = result_income.projections[4]
        
        assert abs(year_5_pension.gross_income - year_5_income.gross_income) < 100


class TestIncomeStreamEndYear:
    """Test that income streams stop at specified end_year."""
    
    def test_income_stops_at_end_year(self):
        """Income with end_year=2038 should not contribute after 2038."""
        
        plan = RetirementPlanInput(
            current_age=60,
            retirement_age=65,
            rrsp_balance=500_000,
            tfsa_balance=0,
            non_registered=0,
            desired_annual_spending=40_000,
            additional_income=[AdditionalIncome(
                monthly_amount=2000,
                start_year=2034,
                indexing_rate=0.0,
                end_year=2038
            )]
        )
        
        result = RetirementCalculator(plan).calculate()
        
        year_2038 = next(p for p in result.projections if p.year == 2038)
        year_2039 = next(p for p in result.projections if p.year == 2039)
        
        income_drop = year_2038.gross_income - year_2039.gross_income
        assert 20000 < income_drop < 28000


class TestNegativeIndexing:
    """Test declining income streams."""
    
    def test_declining_income(self):
        """Income with -10% indexing should decline each year."""
        
        plan = RetirementPlanInput(
            current_age=60,
            retirement_age=65,
            rrsp_balance=500_000,
            tfsa_balance=0,
            non_registered=0,
            desired_annual_spending=40_000,
            additional_income=[AdditionalIncome(
                monthly_amount=3000,
                start_year=2034,
                indexing_rate=-0.10
            )]
        )
        
        result = RetirementCalculator(plan).calculate()
        
        year_0 = next(p for p in result.projections if p.year == 2034)
        year_1 = next(p for p in result.projections if p.year == 2035)
        
        income_drop = (year_0.gross_income - year_1.gross_income) / year_0.gross_income
        assert 0.08 < income_drop < 0.12
