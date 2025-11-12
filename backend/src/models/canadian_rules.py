"""
Canadian retirement rules and constants.
Sources: Government of Canada official documentation.
"""

from enum import Enum
from typing import Dict


class Province(str, Enum):
    """Canadian provinces and territories."""
    ON = "Ontario"
    BC = "British Columbia"
    AB = "Alberta"
    QC = "Quebec"
    MB = "Manitoba"
    SK = "Saskatchewan"
    NS = "Nova Scotia"
    NB = "New Brunswick"
    PE = "Prince Edward Island"
    NL = "Newfoundland and Labrador"
    YT = "Yukon"
    NT = "Northwest Territories"
    NU = "Nunavut"


class CanadianRetirementRules:
    """
    Canadian retirement planning rules and constants.
    
    All values are for 2024/2025 tax year.
    Update annually!
    """
    
    # RRSP/RRIF Rules
    RRSP_CONTRIBUTION_LIMIT_2024 = 31560  # Annual limit
    RRSP_CONVERSION_AGE = 71  # Must convert to RRIF by end of this year
    RRIF_MINIMUM_START_AGE = 72  # First withdrawal year after conversion
    
    # TFSA Rules
    TFSA_CONTRIBUTION_LIMIT_2024 = 7000  # Annual limit
    TFSA_CUMULATIVE_LIMIT_2024 = 95000  # Since 2009
    
    # Government Benefits (Monthly amounts)
    OAS_MAX_MONTHLY_2024 = 713.34  # Ages 65-74
    OAS_MAX_MONTHLY_75_PLUS = 784.67  # Age 75+
    OAS_CLAWBACK_THRESHOLD_2024 = 90997  # Annual income threshold
    OAS_CLAWBACK_RATE = 0.15  # 15% clawback rate
    
    CPP_MAX_MONTHLY_2024 = 1364.60  # At age 65
    CPP_EARLY_REDUCTION_RATE = 0.006  # 0.6% per month before 65
    CPP_LATE_INCREASE_RATE = 0.007  # 0.7% per month after 65
    CPP_EARLIEST_AGE = 60
    CPP_LATEST_AGE = 70
    CPP_NORMAL_AGE = 65
    
    # RRIF Minimum Withdrawal Factors
    # Source: https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/
    #         completing-slips-summaries/t4rsp-t4rif-information-returns/payments/
    #         chart-prescribed-factors.html
    RRIF_FACTORS: Dict[int, float] = {
        55: 0.0286, 56: 0.0291, 57: 0.0297, 58: 0.0303, 59: 0.0309,
        60: 0.0315, 61: 0.0321, 62: 0.0327, 63: 0.0333, 64: 0.0340,
        65: 0.0347, 66: 0.0354, 67: 0.0361, 68: 0.0369, 69: 0.0377,
        70: 0.0385, 71: 0.0528, 72: 0.0540, 73: 0.0553, 74: 0.0567,
        75: 0.0582, 76: 0.0598, 77: 0.0617, 78: 0.0636, 79: 0.0658,
        80: 0.0685, 81: 0.0718, 82: 0.0757, 83: 0.0804, 84: 0.0863,
        85: 0.0938, 86: 0.1033, 87: 0.1157, 88: 0.1330, 89: 0.1533,
        90: 0.1742, 91: 0.1964, 92: 0.2000, 93: 0.2000, 94: 0.2000,
        95: 0.2000  # 20% for age 95+
    }
    
    # Federal Tax Withholding on RRIF Withdrawals (non-Quebec)
    RRIF_WITHHOLDING_FEDERAL = [
        (5000, 0.10),      # Up to $5,000: 10%
        (15000, 0.20),     # $5,001-$15,000: 20%
        (float('inf'), 0.30)  # Over $15,000: 30%
    ]
    
    # Quebec Tax Withholding (different structure)
    RRIF_WITHHOLDING_QUEBEC = [
        (5000, 0.05),
        (15000, 0.10),
        (float('inf'), 0.15)
    ]
    
    @classmethod
    def get_rrif_minimum_factor(cls, age: int) -> float:
        """
        Get RRIF minimum withdrawal factor for a given age.
        
        For ages 70 and under: factor = 1 / (90 - age)
        For ages 71+: use prescribed factors table
        For ages 95+: 20% (0.20)
        
        Args:
            age: Age at beginning of year
            
        Returns:
            Minimum withdrawal factor (as decimal)
        """
        if age < 55:
            raise ValueError("RRIF withdrawals typically don't start before age 55")
        
        if age <= 70:
            return 1 / (90 - age)
        
        if age >= 95:
            return 0.20
        
        return cls.RRIF_FACTORS.get(age, 0.20)
    
    @classmethod
    def calculate_rrif_minimum_withdrawal(cls, balance: float, age: int) -> float:
        """
        Calculate minimum RRIF withdrawal for the year.
        
        Args:
            balance: RRIF balance at beginning of year
            age: Age at beginning of year
            
        Returns:
            Minimum withdrawal amount
        """
        factor = cls.get_rrif_minimum_factor(age)
        return balance * factor
    
    @classmethod
    def calculate_rrif_withholding_tax(
        cls, 
        withdrawal: float, 
        province: Province = Province.ON
    ) -> float:
        """
        Calculate withholding tax on RRIF withdrawal.
        
        Note: This is withholding tax, not final tax liability.
        Actual tax depends on total annual income.
        
        Args:
            withdrawal: Withdrawal amount
            province: Province of residence
            
        Returns:
            Withholding tax amount
        """
        # Use Quebec rates for Quebec
        if province == Province.QC:
            rates = cls.RRIF_WITHHOLDING_QUEBEC
        else:
            rates = cls.RRIF_WITHHOLDING_FEDERAL
        
        # Calculate withholding
        for threshold, rate in rates:
            if withdrawal <= threshold:
                return withdrawal * rate
        
        # Should never reach here
        return withdrawal * 0.30
    
    @classmethod
    def calculate_cpp_adjustment(cls, age: int, base_amount: float) -> float:
        """
        Calculate CPP amount adjusted for taking early or late.
        
        Args:
            age: Age when starting CPP
            base_amount: CPP amount at age 65
            
        Returns:
            Adjusted CPP amount
        """
        if age < cls.CPP_EARLIEST_AGE or age > cls.CPP_LATEST_AGE:
            raise ValueError(f"CPP must be taken between {cls.CPP_EARLIEST_AGE} and {cls.CPP_LATEST_AGE}")
        
        if age < cls.CPP_NORMAL_AGE:
            # Early reduction: 0.6% per month
            months_early = (cls.CPP_NORMAL_AGE - age) * 12
            reduction = months_early * cls.CPP_EARLY_REDUCTION_RATE
            return base_amount * (1 - reduction)
        
        elif age > cls.CPP_NORMAL_AGE:
            # Late increase: 0.7% per month (up to age 70)
            months_late = min((age - cls.CPP_NORMAL_AGE) * 12, 60)  # Max 60 months
            increase = months_late * cls.CPP_LATE_INCREASE_RATE
            return base_amount * (1 + increase)
        
        return base_amount
    
    @classmethod
    def calculate_oas_clawback(cls, annual_income: float, age: int) -> float:
        """
        Calculate OAS clawback based on income.
        
        Args:
            annual_income: Total annual income (MAGI)
            age: Current age
            
        Returns:
            Annual OAS clawback amount
        """
        if annual_income <= cls.OAS_CLAWBACK_THRESHOLD_2024:
            return 0.0
        
        # Calculate base OAS amount
        base_oas = cls.OAS_MAX_MONTHLY_2024 * 12
        if age >= 75:
            base_oas = cls.OAS_MAX_MONTHLY_75_PLUS * 12
        
        # Calculate clawback
        excess_income = annual_income - cls.OAS_CLAWBACK_THRESHOLD_2024
        clawback = excess_income * cls.OAS_CLAWBACK_RATE
        
        # Clawback cannot exceed total OAS
        return min(clawback, base_oas)


# Singleton instance
canadian_rules = CanadianRetirementRules()
