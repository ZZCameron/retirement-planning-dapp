"""
Unit tests for Canadian retirement rules.
"""

import pytest
from backend.src.models.canadian_rules import canadian_rules, Province


class TestRRIFRules:
    """Test RRIF withdrawal rules."""
    
    def test_rrif_factor_age_71(self):
        """Test RRIF factor at age 71."""
        factor = canadian_rules.get_rrif_minimum_factor(71)
        assert factor == 0.0528
    
    def test_rrif_factor_age_65(self):
        """Test RRIF factor for age 65 (calculated)."""
        factor = canadian_rules.get_rrif_minimum_factor(65)
        expected = 1 / (90 - 65)
        assert abs(factor - expected) < 0.0001
    
    def test_rrif_factor_age_95_plus(self):
        """Test RRIF factor for age 95+ is capped at 20%."""
        assert canadian_rules.get_rrif_minimum_factor(95) == 0.20
        assert canadian_rules.get_rrif_minimum_factor(100) == 0.20
    
    def test_rrif_minimum_withdrawal(self):
        """Test RRIF minimum withdrawal calculation."""
        balance = 100000
        age = 71
        withdrawal = canadian_rules.calculate_rrif_minimum_withdrawal(balance, age)
        expected = 100000 * 0.0528
        assert withdrawal == expected


class TestCPPRules:
    """Test CPP adjustment rules."""
    
    def test_cpp_at_normal_age(self):
        """Test CPP at age 65 (no adjustment)."""
        base_amount = 1000
        adjusted = canadian_rules.calculate_cpp_adjustment(65, base_amount)
        assert adjusted == base_amount
    
    def test_cpp_early_at_60(self):
        """Test CPP taken at age 60 (36% reduction)."""
        base_amount = 1000
        adjusted = canadian_rules.calculate_cpp_adjustment(60, base_amount)
        # 60 months early * 0.6% = 36% reduction
        expected = base_amount * (1 - 0.36)
        assert abs(adjusted - expected) < 1.0
    
    def test_cpp_delayed_to_70(self):
        """Test CPP delayed to age 70 (42% increase)."""
        base_amount = 1000
        adjusted = canadian_rules.calculate_cpp_adjustment(70, base_amount)
        # 60 months late * 0.7% = 42% increase
        expected = base_amount * (1 + 0.42)
        assert abs(adjusted - expected) < 1.0
    
    def test_cpp_invalid_age_raises_error(self):
        """Test CPP with invalid age raises error."""
        with pytest.raises(ValueError):
            canadian_rules.calculate_cpp_adjustment(55, 1000)


class TestWithholdingTax:
    """Test RRIF withholding tax calculations."""
    
    def test_withholding_small_amount(self):
        """Test withholding on small withdrawal."""
        tax = canadian_rules.calculate_rrif_withholding_tax(3000, Province.ON)
        expected = 3000 * 0.10
        assert tax == expected
    
    def test_withholding_medium_amount(self):
        """Test withholding on medium withdrawal."""
        tax = canadian_rules.calculate_rrif_withholding_tax(10000, Province.ON)
        expected = 10000 * 0.20
        assert tax == expected
    
    def test_withholding_large_amount(self):
        """Test withholding on large withdrawal."""
        tax = canadian_rules.calculate_rrif_withholding_tax(20000, Province.ON)
        expected = 20000 * 0.30
        assert tax == expected
