"""
Canadian provincial tax calculator.

Calculates federal and provincial income taxes for Canadian provinces.
Tax brackets and rates for 2024 tax year.

Usage:
    from models.tax_calculator import calculate_canadian_tax
    
    result = calculate_canadian_tax(taxable_income=75000, province="Ontario")
    print(f"Total tax: ${result['total_tax']}")
"""

from enum import Enum
from typing import Dict, List, Tuple


class Province(str, Enum):
    """Canadian provinces and territories"""
    ONTARIO = "Ontario"
    BRITISH_COLUMBIA = "British Columbia"
    ALBERTA = "Alberta"
    QUEBEC = "Quebec"
    MANITOBA = "Manitoba"
    SASKATCHEWAN = "Saskatchewan"
    NOVA_SCOTIA = "Nova Scotia"
    NEW_BRUNSWICK = "New Brunswick"
    PRINCE_EDWARD_ISLAND = "Prince Edward Island"
    NEWFOUNDLAND_AND_LABRADOR = "Newfoundland and Labrador"


class TaxCalculator:
    """
    Calculate Canadian income taxes (federal + provincial).
    
    Based on 2024 tax year rates.
    Includes basic personal amounts (non-refundable tax credits).
    """
    
    # Federal tax brackets 2024
    # Format: (upper_limit, marginal_rate)
    FEDERAL_BRACKETS = [
        (55867, 0.15),       # First $55,867 at 15%
        (111733, 0.205),     # $55,867 to $111,733 at 20.5%
        (173205, 0.26),      # $111,733 to $173,205 at 26%
        (246752, 0.29),      # $173,205 to $246,752 at 29%
        (float('inf'), 0.33) # Over $246,752 at 33%
    ]
    
    FEDERAL_BASIC_PERSONAL_AMOUNT = 15000  # 2024 federal BPA
    
    # Provincial tax brackets 2024
    # Format: {Province: [(upper_limit, marginal_rate), ...]}
    PROVINCIAL_BRACKETS = {
        Province.ONTARIO: [
            (49231, 0.0505),
            (98463, 0.0915),
            (150000, 0.1116),
            (220000, 0.1216),
            (float('inf'), 0.1316)
        ],
        Province.BRITISH_COLUMBIA: [
            (45654, 0.0506),
            (91310, 0.077),
            (104835, 0.105),
            (127299, 0.1229),
            (172602, 0.147),
            (240716, 0.168),
            (float('inf'), 0.205)
        ],
        Province.ALBERTA: [
            (142292, 0.10),
            (170751, 0.12),
            (227668, 0.13),
            (341502, 0.14),
            (float('inf'), 0.15)
        ],
        Province.QUEBEC: [
            (49275, 0.15),
            (98540, 0.20),
            (119910, 0.24),
            (float('inf'), 0.2575)
        ],
        Province.MANITOBA: [
            (36842, 0.108),
            (79625, 0.1275),
            (float('inf'), 0.174)
        ],
        Province.SASKATCHEWAN: [
            (49720, 0.105),
            (142058, 0.125),
            (float('inf'), 0.145)
        ],
        Province.NOVA_SCOTIA: [
            (29590, 0.0879),
            (59180, 0.1495),
            (93000, 0.1667),
            (150000, 0.175),
            (float('inf'), 0.21)
        ],
        Province.NEW_BRUNSWICK: [
            (47715, 0.094),
            (95431, 0.14),
            (176756, 0.16),
            (float('inf'), 0.195)
        ],
        Province.PRINCE_EDWARD_ISLAND: [
            (31984, 0.098),
            (63969, 0.138),
            (float('inf'), 0.167)
        ],
        Province.NEWFOUNDLAND_AND_LABRADOR: [
            (41457, 0.087),
            (82913, 0.145),
            (148027, 0.158),
            (207239, 0.173),
            (264750, 0.183),
            (529500, 0.193),
            (1059000, 0.198),
            (float('inf'), 0.208)
        ],
    }
    
    # Provincial basic personal amounts 2024
    PROVINCIAL_BASIC_AMOUNTS = {
        Province.ONTARIO: 11865,
        Province.BRITISH_COLUMBIA: 12580,
        Province.ALBERTA: 21885,
        Province.QUEBEC: 17183,
        Province.MANITOBA: 15000,
        Province.SASKATCHEWAN: 17661,
        Province.NOVA_SCOTIA: 8481,
        Province.NEW_BRUNSWICK: 12458,
        Province.PRINCE_EDWARD_ISLAND: 12000,
        Province.NEWFOUNDLAND_AND_LABRADOR: 10382,
    }
    
    @classmethod
    def calculate_tax(cls, taxable_income: float, province: Province) -> Dict[str, float]:
        """
        Calculate total tax owing (federal + provincial).
        
        Args:
            taxable_income: Annual taxable income before deductions
            province: Province of residence
            
        Returns:
            Dictionary containing:
            - federal_tax: Federal tax owing
            - provincial_tax: Provincial tax owing
            - total_tax: Combined tax owing
            - effective_rate: Effective tax rate as percentage
            - marginal_rate: Marginal tax rate as percentage
        """
        if taxable_income <= 0:
            return {
                "federal_tax": 0.0,
                "provincial_tax": 0.0,
                "total_tax": 0.0,
                "effective_rate": 0.0,
                "marginal_rate": 0.0
            }
        
        # Apply basic personal amounts (they reduce taxable income)
        federal_taxable = max(0, taxable_income - cls.FEDERAL_BASIC_PERSONAL_AMOUNT)
        provincial_basic = cls.PROVINCIAL_BASIC_AMOUNTS.get(province, 10000)
        provincial_taxable = max(0, taxable_income - provincial_basic)
        
        # Calculate federal tax
        federal_tax = cls._calculate_bracket_tax(federal_taxable, cls.FEDERAL_BRACKETS)
        federal_marginal = cls._get_marginal_rate(federal_taxable, cls.FEDERAL_BRACKETS)
        
        # Calculate provincial tax
        provincial_brackets = cls.PROVINCIAL_BRACKETS.get(province, [(float('inf'), 0.10)])
        provincial_tax = cls._calculate_bracket_tax(provincial_taxable, provincial_brackets)
        provincial_marginal = cls._get_marginal_rate(provincial_taxable, provincial_brackets)
        
        total_tax = federal_tax + provincial_tax
        marginal_rate = federal_marginal + provincial_marginal
        
        return {
            "federal_tax": round(federal_tax, 2),
            "provincial_tax": round(provincial_tax, 2),
            "total_tax": round(total_tax, 2),
            "effective_rate": round((total_tax / taxable_income * 100), 2),
            "marginal_rate": round(marginal_rate * 100, 2)
        }
    
    @staticmethod
    def _calculate_bracket_tax(income: float, brackets: list) -> float:
        """
        Calculate tax using progressive marginal brackets.
        
        Args:
            income: Taxable income
            brackets: List of (upper_limit, rate) tuples
            
        Returns:
            Total tax owing
        """
        if income <= 0:
            return 0.0
        
        tax = 0.0
        previous_limit = 0
        
        for limit, rate in brackets:
            if income <= limit:
                # Income falls within this bracket
                taxable_in_bracket = income - previous_limit
                tax += taxable_in_bracket * rate
                break
            else:
                # Income exceeds this bracket, tax the full bracket
                taxable_in_bracket = limit - previous_limit
                tax += taxable_in_bracket * rate
                previous_limit = limit
        
        return tax
    
    @staticmethod
    def _get_marginal_rate(income: float, brackets: list) -> float:
        """
        Get marginal tax rate for given income level.
        
        Args:
            income: Taxable income
            brackets: List of (upper_limit, rate) tuples
            
        Returns:
            Marginal rate (as decimal, e.g., 0.26 for 26%)
        """
        if income <= 0:
            return 0.0
        
        for limit, rate in brackets:
            if income <= limit:
                return rate
        
        # Default to highest bracket
        return brackets[-1][1]
    
def calculate_canadian_tax(taxable_income: float, province: str) -> Dict[str, float]:
    """
    Convenience function to calculate Canadian taxes.
    
    Args:
        taxable_income: Annual taxable income in CAD
        province: Province name as string (e.g., "Ontario", "Alberta")
        
    Returns:
        Dictionary with detailed tax breakdown
    """
    # Convert province string to enum
    try:
        province_enum = Province(province)
    except ValueError:
        # Handle case-insensitive and underscore variations
        province_upper = province.upper().replace(" ", "_")
        province_enum = Province[province_upper]
    
    # Calculate taxes using the class method
    result = TaxCalculator.calculate_tax(taxable_income, province_enum)
    
    # Add after_tax_income to the result
    total_tax = result['total_tax']
    after_tax_income = taxable_income - total_tax
    
    result['after_tax_income'] = after_tax_income
    result['income'] = taxable_income
    
    return result
