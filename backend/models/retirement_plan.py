"""
Data models for retirement planning API.
Using Pydantic v2 for validation.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum

from .canadian_rules import Province

class TaxCalculationMode(str, Enum):
    """
    Tax calculation accuracy mode.
    
    SIMPLIFIED: Free tier - uses flat 25% rate (fast, less accurate)
    ACCURATE: Premium tier - uses provincial tax calculator (accurate, recommended)
    """
    SIMPLIFIED = "simplified"
    ACCURATE = "accurate"
    
class PensionIncome(BaseModel):
    """
    Single pension income stream with indexing.
    
    For current pensions: Set start_year to current year (2024/2025)
    For future pensions: Set start_year to when pension begins
    Indexing applies from start_year forward using compound interest.
    """
    monthly_amount: float = Field(
        gt=0,
        description="Current or expected monthly pension amount (CAD, gross)"
    )
    start_year: int = Field(
        ge=2024,
        le=2100,
        description="Year pension starts (use current year if already receiving)"
    )
    end_year: Optional[int] = Field(
        default=None,
        description="Year pension ends (None = lifetime pension)"
    )
    indexing_rate: float = Field(
        default=0.0,
        ge=-5.0,
        le=10.0,
        description="Annual indexing rate (decimal, e.g., 0.02 for 2%)"
    )


class AdditionalIncome(BaseModel):
    """
    Additional income stream (rental, consulting, royalties, etc.)
    Starts at retirement or specified year, can grow/decline, optional end year
    """
    monthly_amount: float = Field(
        ...,
        description="Monthly income amount (CAD, gross)",
        gt=0
    )
    start_year: int = Field(
        ...,
        description="Year income starts (typically retirement year)"
    )
    indexing_rate: float = Field(
        default=0.0,
        description="Annual growth/decline rate (0.02 = 2% growth, -0.05 = 5% decline)"
    )
    end_year: Optional[int] = Field(
        default=None,
        description="Year income ends (None = continues for life)"
    )

    
    @field_validator("end_year")
    @classmethod
    def validate_end_year(cls, v: Optional[int], info) -> Optional[int]:
        """Ensure end year is after start year if provided."""
        if v is not None:
            start_year = info.data.get("start_year")
            if start_year and v <= start_year:
                raise ValueError("Pension end_year must be after start_year")
        return v



class RealEstateHolding(BaseModel):
    """
    Single real estate property.
    Types: primary_residence, cottage, rental, investment
    """
    value: float = Field(
        gt=0,
        description="Current property value (CAD)"
    )
    real_return: float = Field(
        default=0.01,
        ge=-0.10,
        le=0.15,
        description="Real appreciation rate after inflation (decimal)"
    )
    sale_age: int = Field(
        ge=0,
        le=150,
        description="Age when property will be sold (0 = never sell)"
    )
    property_type: str = Field(
        default="primary_residence",
        description="Type: primary_residence, cottage, rental, investment"
    )

class RetirementPlanInput(BaseModel):
    """Input data for retirement planning calculations."""
    
    # Personal Information
    current_age: int = Field(ge=18, le=100, description="Current age")
    retirement_age: int = Field(ge=55, le=75, description="Planned retirement age")
    life_expectancy: int = Field(ge=65, le=150, description="Expected lifespan")
    province: Province = Field(description="Province of residence")
    
    # Current Balances
    rrsp_balance: float = Field(ge=0, description="Current RRSP balance (CAD)")
    tfsa_balance: float = Field(ge=0, default=0, description="Current TFSA balance (CAD)")
    non_registered: float = Field(ge=0, default=0, description="Non-registered investments (CAD)")
    
    # Contributions
    monthly_contribution: float = Field(
        ge=0, 
        le=10000, 
        description="Monthly contribution to retirement savings (CAD)"
    )
    
    # Asset-Specific Real Returns (After Inflation)
    rrsp_real_return: float = Field(
        default=0.02,
        ge=-0.10,
        le=0.15,
        description="RRSP/RRIF real return after inflation (decimal, e.g., 0.02 for 2%)"
    )
    tfsa_real_return: float = Field(
        default=0.04,
        ge=-0.10,
        le=0.15,
        description="TFSA real return after inflation (decimal, e.g., 0.04 for 4%)"
    )
    non_reg_real_return: float = Field(
        default=0.05,
        ge=-0.10,
        le=0.15,
        description="Non-registered real return after inflation (decimal, e.g., 0.05 for 5%)"
    )
    
    # Real Estate (Optional)
    real_estate_holdings: List[RealEstateHolding] = Field(
        default_factory=list,
        description="List of real estate properties (primary residence, cottage, rental, etc.)"
    )
    
    # Government Benefits
    cpp_monthly: float = Field(
        ge=0,
        le=2000,
        description="Expected monthly CPP benefit at age 65 (CAD)"
    )
    cpp_start_age: int = Field(
        default=65,
        ge=60,
        le=70,
        description="Age to start CPP"
    )
    oas_start_age: int = Field(
        default=65,
        ge=65,
        le=70,
        description="Age to start OAS"
    )
        
    # Pension Income (Optional)
    pensions: List[PensionIncome] = Field(
        default_factory=list,
        description="List of pension income streams (can have multiple)"
    )
    additional_income: List[AdditionalIncome] = Field(
        default_factory=list,
        description="Additional income streams (rental, consulting, etc.)"
    )

    # Retirement Spending
    desired_annual_spending: float = Field(
        ge=0,
        description="Desired annual spending in retirement (today's dollars, CAD)"
    )
    
    # Spouse (Optional)
    has_spouse: bool = Field(default=False)
    spouse_age: Optional[int] = Field(default=None, ge=18, le=100)
    
    @field_validator("retirement_age")
    @classmethod
    def validate_retirement_age(cls, v: int, info) -> int:
        """Ensure retirement age is at or after current age."""
        current_age = info.data.get("current_age")
        if current_age and v < current_age:  # Changed <= to <
            raise ValueError("Retirement age must be greater than or equal to current age")
        return v
    
    @field_validator("life_expectancy")
    @classmethod
    def validate_life_expectancy(cls, v: int, info) -> int:
        """Ensure life expectancy is reasonable."""
        retirement_age = info.data.get("retirement_age")
        if retirement_age and v <= retirement_age:
            raise ValueError("Life expectancy must be greater than retirement age")
        return v
    
    @field_validator("spouse_age")
    @classmethod
    def validate_spouse_age(cls, v: Optional[int], info) -> Optional[int]:
        """Validate spouse age if has_spouse is True."""
        has_spouse = info.data.get("has_spouse")
        if has_spouse and v is None:
            raise ValueError("Must provide spouse_age when has_spouse is True")
        return v
    
    # Tax calculation mode (default to free tier)
    tax_calculation_mode: TaxCalculationMode = Field(
        default=TaxCalculationMode.SIMPLIFIED,
        description="Tax calculation accuracy: 'simplified' (25% flat) or 'accurate' (provincial)"
    )
    
    # Province (only used if tax_calculation_mode == ACCURATE)
    # Note: 'province' field may already exist - check first!
    # If it exists, just update the description to mention it's used for accurate tax mode


class IncomeBreakdown(BaseModel):
    """Detailed breakdown of income sources for enhanced insights."""
    rrif_withdrawal: float = 0.0
    tfsa_withdrawal: float = 0.0
    cpp_income: float = 0.0
    oas_income: float = 0.0
    pension_total: float = 0.0
    additional_income_total: float = 0.0
    # Per-stream details
    pension_streams: List[dict] = Field(default_factory=list)
    additional_income_streams: List[dict] = Field(default_factory=list)

class YearlyProjection(BaseModel):
    """Financial projection for a single year."""
    
    year: int = Field(description="Year number (0 = current year)")
    age: int = Field(description="Age at beginning of year")
    
    # Account Balances
    rrsp_rrif_balance: float = Field(description="RRSP/RRIF balance")
    tfsa_balance: float = Field(description="TFSA balance")
    non_registered_balance: float = Field(description="Non-registered balance")
    total_balance: float = Field(description="Total portfolio value")
    
    # Income & Withdrawals
    rrif_withdrawal: float = Field(default=0, description="RRIF withdrawal (if applicable)")
    cpp_income: float = Field(default=0, description="CPP income")
    oas_income: float = Field(default=0, description="OAS income (after clawback)")
    other_withdrawals: float = Field(default=0, description="Other account withdrawals")
    
    # Spending & Taxes
    gross_income: float = Field(description="Total gross income")
    taxes_estimated: float = Field(description="Estimated taxes")
    net_income: float = Field(description="After-tax income")
    spending: float = Field(description="Annual spending (inflation-adjusted)")
    
    # Enhanced insights (optional, only included in paid version)
    income_breakdown: Optional[IncomeBreakdown] = None


class RetirementPlanOutput(BaseModel):
    """Complete retirement plan projection output."""
    
    # Input Echo
    input_summary: RetirementPlanInput
    
    # Timeline
    years_to_retirement: int
    retirement_duration: int
    total_years: int
    
    # Projections
    projections: list[YearlyProjection]
    
    # Summary Statistics
    total_contributions: float = Field(description="Total contributions during accumulation")
    final_balance: float = Field(description="Balance at life expectancy")
    success: bool = Field(description="Whether plan is financially viable")
    
    # Warnings & Recommendations
    warnings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class HealthCheckResponse(BaseModel):
    """Health check endpoint response."""
    
    status: str
    version: str
    environment: str
