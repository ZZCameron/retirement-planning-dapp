"""
Data models for retirement planning API.
Using Pydantic v2 for validation.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator

from .canadian_rules import Province


class RetirementPlanInput(BaseModel):
    """Input data for retirement planning calculations."""
    
    # Personal Information
    current_age: int = Field(ge=18, le=100, description="Current age")
    retirement_age: int = Field(ge=55, le=75, description="Planned retirement age")
    life_expectancy: int = Field(ge=65, le=120, description="Expected lifespan")
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
    
    # Returns and Inflation
    expected_return: float = Field(
        ge=0.0, 
        le=0.25, 
        description="Expected annual return (decimal, e.g., 0.07 for 7%)"
    )
    expected_inflation: float = Field(
        default=0.025,
        ge=0.0,
        le=0.10,
        description="Expected inflation rate (decimal)"
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
        """Ensure retirement age is after current age."""
        current_age = info.data.get("current_age")
        if current_age and v <= current_age:
            raise ValueError("Retirement age must be greater than current age")
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
