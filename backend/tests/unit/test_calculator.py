"""
Unit tests for retirement calculator.
"""

import pytest
from backend.src.services.retirement_calculator import calculator


class TestRetirementCalculator:
    """Test retirement calculator service."""
    
    def test_calculate_plan_basic(self, sample_plan_input):
        """Test basic retirement plan calculation."""
        result = calculator.calculate_plan(sample_plan_input)
        
        # Check basic structure
        assert result.years_to_retirement == 30
        assert result.retirement_duration == 25
        assert result.total_years == 55
        assert len(result.projections) == 56  # 0 to 55 inclusive
        
        # Check first projection (current year)
        first_proj = result.projections[0]
        assert first_proj.year == 0
        assert first_proj.age == 35
        assert first_proj.rrsp_rrif_balance > 0
    
    def test_final_balance_positive(self, sample_plan_input):
        """Test that plan results in positive final balance."""
        result = calculator.calculate_plan(sample_plan_input)
        
        # With reasonable inputs, should have money left
        assert result.final_balance > 0
        assert result.success == True
    
    def test_rrif_withdrawal_starts_at_72(self, sample_plan_input):
        """Test that RRIF withdrawals start at age 72."""
        result = calculator.calculate_plan(sample_plan_input)
        
        # Find projection at age 72
        proj_72 = next(p for p in result.projections if p.age == 72)
        assert proj_72.rrif_withdrawal > 0
        
        # Age 71 should have no RRIF withdrawal
        proj_71 = next(p for p in result.projections if p.age == 71)
        assert proj_71.rrif_withdrawal == 0
    
    def test_cpp_starts_at_specified_age(self, sample_plan_input):
        """Test that CPP starts at specified age."""
        result = calculator.calculate_plan(sample_plan_input)
        
        # Find projection at CPP start age
        cpp_start = sample_plan_input.cpp_start_age
        proj_cpp_start = next(p for p in result.projections if p.age == cpp_start)
        assert proj_cpp_start.cpp_income > 0
        
        # Year before should have no CPP
        proj_before_cpp = next(p for p in result.projections if p.age == cpp_start - 1)
        assert proj_before_cpp.cpp_income == 0
