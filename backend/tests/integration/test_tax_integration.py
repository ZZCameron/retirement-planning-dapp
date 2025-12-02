"""
Integration tests for tax calculation modes and retirement projections.

These tests verify the interaction between:
- Tax calculator (backend/models/tax_calculator.py)
- Retirement calculator (backend/services/retirement_calculator.py)
- Tax calculation modes (SIMPLIFIED vs ACCURATE)
"""

import pytest
from backend.models.retirement_plan import RetirementPlanInput, TaxCalculationMode
from backend.services.retirement_calculator import RetirementCalculator


@pytest.fixture
def base_retirement_input():
    """Standard retirement scenario for testing."""
    return {
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


@pytest.fixture
def calculator():
    """Retirement calculator instance."""
    return RetirementCalculator()


class TestTaxCalculationModes:
    """Test SIMPLIFIED vs ACCURATE tax calculation modes."""
    
    def test_simplified_vs_accurate_different_results(self, base_retirement_input, calculator):
        """ACCURATE mode should yield different final balance than SIMPLIFIED."""
        # Arrange
        simplified_input = RetirementPlanInput(
            **base_retirement_input, 
            tax_calculation_mode=TaxCalculationMode.SIMPLIFIED
        )
        accurate_input = RetirementPlanInput(
            **base_retirement_input, 
            tax_calculation_mode=TaxCalculationMode.ACCURATE
        )
        
        # Act
        result_simplified = calculator.calculate_plan(simplified_input)
        result_accurate = calculator.calculate_plan(accurate_input)
        
        # Assert
        assert result_simplified.final_balance != result_accurate.final_balance, \
            "SIMPLIFIED and ACCURATE modes should produce different final balances"
        
        # ACCURATE should be better (more money remaining)
        assert result_accurate.final_balance > result_simplified.final_balance, \
            f"ACCURATE mode should leave more money: " \
            f"ACCURATE=${result_accurate.final_balance:,.0f} vs " \
            f"SIMPLIFIED=${result_simplified.final_balance:,.0f}"
    
    def test_accurate_mode_tax_benefit_persists(self, base_retirement_input, calculator):
        """ACCURATE mode benefit should persist throughout retirement."""
        # Arrange
        simplified_input = RetirementPlanInput(
            **base_retirement_input, 
            tax_calculation_mode=TaxCalculationMode.SIMPLIFIED
        )
        accurate_input = RetirementPlanInput(
            **base_retirement_input, 
            tax_calculation_mode=TaxCalculationMode.ACCURATE
        )
        
        # Act
        result_simplified = calculator.calculate_plan(simplified_input)
        result_accurate = calculator.calculate_plan(accurate_input)
        
        # Assert - Check benefit at multiple ages
        test_ages = [65, 70, 75, 80, 85, 90]
        for age in test_ages:
            simp_year = next((y for y in result_simplified.projections if y.age == age), None)
            acc_year = next((y for y in result_accurate.projections if y.age == age), None)
            
            if simp_year and acc_year:
                # ACCURATE should have more or equal balance at all ages
                assert acc_year.total_balance >= simp_year.total_balance, \
                    f"Age {age}: ACCURATE mode should maintain advantage " \
                    f"(ACCURATE=${acc_year.total_balance:,.0f} vs " \
                    f"SIMPLIFIED=${simp_year.total_balance:,.0f})"
    
    def test_tax_savings_magnitude(self, base_retirement_input, calculator):
        """ACCURATE mode should save at least $2000 over retirement."""
        # Arrange
        simplified_input = RetirementPlanInput(
            **base_retirement_input, 
            tax_calculation_mode=TaxCalculationMode.SIMPLIFIED
        )
        accurate_input = RetirementPlanInput(
            **base_retirement_input, 
            tax_calculation_mode=TaxCalculationMode.ACCURATE
        )
        
        # Act
        result_simplified = calculator.calculate_plan(simplified_input)
        result_accurate = calculator.calculate_plan(accurate_input)
        
        # Assert
        savings = result_accurate.final_balance - result_simplified.final_balance
        assert savings >= 2000, \
            f"ACCURATE mode should save at least $2,000 (actual: ${savings:,.0f})"


class TestTFSADepletion:
    """Test behavior when TFSA is depleted."""
    
    def test_tfsa_depletion_triggers_rrsp_withdrawal(self, calculator):
        """When TFSA depletes, system should withdraw from RRSP."""
        # Arrange - scenario where TFSA will deplete early
        input_data = RetirementPlanInput(
            current_age=60,
            retirement_age=65,
            life_expectancy=90,
            province="Ontario",
            rrsp_balance=200000,
            tfsa_balance=100000,
            non_registered=0,
            monthly_contribution=0,
            expected_return=0.06,
            expected_inflation=0.025,
            desired_annual_spending=45000,
            cpp_start_age=65,
            cpp_monthly=1200,
            oas_start_age=65,
            has_spouse=False,
            tax_calculation_mode=TaxCalculationMode.ACCURATE
        )
        
        # Act
        result = calculator.calculate_plan(input_data)
        
        # Find when TFSA depletes
        tfsa_depletion_age = None
        for year in result.projections:
            if year.tfsa_balance == 0 and tfsa_depletion_age is None:
                tfsa_depletion_age = year.age
                break
        
        # Assert
        assert tfsa_depletion_age is not None, "TFSA should deplete in this scenario"
        
        # After TFSA depletion, check that RRSP withdrawals increase
        year_before = next(y for y in result.projections if y.age == tfsa_depletion_age - 1)
        year_after = next(y for y in result.projections if y.age == tfsa_depletion_age + 1)
        
        assert year_after.other_withdrawals > 0 or year_after.rrif_withdrawal > year_before.rrif_withdrawal, \
            "After TFSA depletion, should increase RRSP withdrawals"


class TestRRSPOverdraftPrevention:
    """Test that RRSP balance never goes negative."""
    
    def test_no_negative_rrsp_balance(self, base_retirement_input, calculator):
        """RRSP balance should never go negative, even when funds are low."""
        # Arrange - aggressive scenario
        aggressive_input = base_retirement_input.copy()
        aggressive_input["desired_annual_spending"] = 80000  # High spending
        
        input_data = RetirementPlanInput(
            **aggressive_input,
            tax_calculation_mode=TaxCalculationMode.ACCURATE
        )
        
        # Act
        result = calculator.calculate_plan(input_data)
        
        # Assert
        for year in result.projections:
            assert year.rrsp_rrif_balance >= 0, \
                f"Age {year.age}: RRSP balance went negative " \
                f"(${year.rrsp_rrif_balance:,.0f})"
            assert year.tfsa_balance >= 0, \
                f"Age {year.age}: TFSA balance went negative " \
                f"(${year.tfsa_balance:,.0f})"
            assert year.non_registered_balance >= 0, \
                f"Age {year.age}: Non-registered balance went negative " \
                f"(${year.non_registered_balance:,.0f})"
    
    def test_total_balance_never_negative(self, calculator):
        """Total balance across all accounts should never go negative."""
        # Arrange - low balance scenario
        input_data = RetirementPlanInput(
            current_age=60,
            retirement_age=65,
            life_expectancy=80,
            province="Ontario",
            rrsp_balance=50000,  # Low starting balance
            tfsa_balance=20000,
            non_registered=0,
            monthly_contribution=0,
            expected_return=0.06,
            expected_inflation=0.025,
            desired_annual_spending=45000,  # High spending
            cpp_start_age=65,
            cpp_monthly=1200,
            oas_start_age=65,
            has_spouse=False,
            tax_calculation_mode=TaxCalculationMode.ACCURATE
        )
        
        # Act
        result = calculator.calculate_plan(input_data)
        
        # Assert - All balances should be >= 0
        for year in result.projections:
            assert year.total_balance >= 0, \
                f"Age {year.age}: Total balance went negative (${year.total_balance:,.0f})"
            
            # Individual account balances
            assert year.rrsp_rrif_balance >= 0, \
                f"Age {year.age}: RRSP went negative (${year.rrsp_rrif_balance:,.0f})"
            assert year.tfsa_balance >= 0, \
                f"Age {year.age}: TFSA went negative (${year.tfsa_balance:,.0f})"
            assert year.non_registered_balance >= 0, \
                f"Age {year.age}: Non-reg went negative (${year.non_registered_balance:,.0f})"


class TestTaxCalculationAccuracy:
    """Test tax calculation accuracy across scenarios."""
    
    def test_accurate_vs_simplified_tax_difference(self, calculator):
        """ACCURATE mode should calculate lower taxes than SIMPLIFIED for typical income."""
        # Arrange - scenario with ~$50k taxable income
        input_data_simplified = RetirementPlanInput(
            current_age=64,
            retirement_age=65,
            life_expectancy=66,
            province="Ontario",
            rrsp_balance=200000,
            tfsa_balance=0,
            non_registered=0,
            monthly_contribution=0,
            expected_return=0.0,
            expected_inflation=0.0,
            desired_annual_spending=30000,
            cpp_start_age=65,
            cpp_monthly=1200,
            oas_start_age=65,
            has_spouse=False,
            tax_calculation_mode=TaxCalculationMode.SIMPLIFIED
        )
        
        input_data_accurate = RetirementPlanInput(
            current_age=64,
            retirement_age=65,
            life_expectancy=66,
            province="Ontario",
            rrsp_balance=200000,
            tfsa_balance=0,
            non_registered=0,
            monthly_contribution=0,
            expected_return=0.0,
            expected_inflation=0.0,
            desired_annual_spending=30000,
            cpp_start_age=65,
            cpp_monthly=1200,
            oas_start_age=65,
            has_spouse=False,
            tax_calculation_mode=TaxCalculationMode.ACCURATE
        )
        
        # Act
        result_simplified = calculator.calculate_plan(input_data_simplified)
        result_accurate = calculator.calculate_plan(input_data_accurate)
        
        year_simp = next(y for y in result_simplified.projections if y.age == 65)
        year_acc = next(y for y in result_accurate.projections if y.age == 65)
        
        # Assert - ACCURATE should calculate lower taxes for this income level
        assert year_acc.taxes_estimated < year_simp.taxes_estimated, \
            f"ACCURATE mode should calculate lower taxes: " \
            f"ACCURATE=${year_acc.taxes_estimated:,.0f} vs " \
            f"SIMPLIFIED=${year_simp.taxes_estimated:,.0f}"
        
        # Tax difference should be meaningful (at least $500)
        tax_savings = year_simp.taxes_estimated - year_acc.taxes_estimated
        assert tax_savings >= 500, \
            f"Tax savings should be at least $500 (actual: ${tax_savings:,.0f})"


if __name__ == "__main__":
    # Allow running this file directly for quick testing
    pytest.main([__file__, "-v", "--tb=short"])
