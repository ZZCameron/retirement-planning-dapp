"""
Batch retirement planning models for scenario analysis.
Supports min/max ranges with enable/disable per field.
"""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

from backend.models.retirement_plan import PensionIncome, RealEstateHolding


class RangeField(BaseModel):
    """
    Represents a field that can be either single value or min/max range.
    When enabled=False, uses min value only.
    When enabled=True, generates [min, max] for scenarios.
    """
    min: float
    max: Optional[float] = None
    enabled: bool = False
    
    @field_validator('max')
    def validate_max(cls, v, info):
        if v is not None and 'min' in info.data and v < info.data['min']:
            raise ValueError("Max must be >= min")
        return v
    
    def get_values(self) -> List[float]:
        """Return list of values to iterate over."""
        if not self.enabled or self.max is None:
            return [self.min]
        return [self.min, self.max]


class PensionIncome(BaseModel):
    """Pension income configuration."""
    enabled: bool = False
    monthly_amount: float = Field(default=0, ge=0, le=10000)
    start_year: int = Field(default=2025)
    annual_indexing: float = Field(default=0.02, ge=0.0, le=0.1)
    
    @field_validator('start_year')
    def validate_start_year(cls, v):
        current_year = datetime.now().year
        if v < current_year - 50:
            raise ValueError("Start year too far in the past")
        if v > current_year + 50:
            raise ValueError("Start year too far in the future")
        return v


class BatchRetirementPlanInput(BaseModel):
    """
    Input model for batch retirement calculations.
    Single-value fields and range fields with enable/disable.
    """
    # Single value fields
    current_age: int = Field(ge=18, le=85)
    life_expectancy: int = Field(ge=65, le=150)
    province: str
    real_estate_holdings: List[RealEstateHolding] = Field(default_factory=list)
    
    # Range fields (enabled = vary this field)
    retirement_age: RangeField
    rrsp_balance: RangeField
    tfsa_balance: RangeField
    nonreg_balance: RangeField
    annual_spending: RangeField
    monthly_savings: RangeField
    
    rrsp_real_return: RangeField
    tfsa_real_return: RangeField
    nonreg_real_return: RangeField
    
    real_estate_appreciation: RangeField
    real_estate_sale_age: RangeField
    
    cpp_start_age: RangeField
    oas_start_age: RangeField
    
    # Pension (single values, not ranged)
    pensions: List[PensionIncome] = Field(default_factory=list)
    
    @field_validator('life_expectancy')
    def validate_life_expectancy(cls, v, info):
        if 'current_age' in info.data and v <= info.data['current_age']:
            raise ValueError("Life expectancy must be > current age")
        return v
    
    def count_enabled_fields(self) -> int:
        """Count how many range fields are enabled."""
        fields = [
            self.retirement_age, self.rrsp_balance, self.tfsa_balance,
            self.nonreg_balance, self.annual_spending, self.monthly_savings,
            self.rrsp_real_return, self.tfsa_real_return, self.nonreg_real_return,
            self.real_estate_appreciation, self.real_estate_sale_age,
            self.cpp_start_age, self.oas_start_age
        ]
        return sum(1 for f in fields if f.enabled)
    
    def estimate_scenario_count(self) -> int:
        """Calculate total number of scenarios."""
        return 2 ** self.count_enabled_fields()


class ScenarioResult(BaseModel):
    """Single scenario result with year-by-year data."""
    scenario_id: int
    
    # Input parameters for this scenario
    retirement_age: int
    rrsp_balance: float
    tfsa_balance: float
    nonreg_balance: float
    annual_spending: float
    monthly_savings: float
    rrsp_real_return: float
    tfsa_real_return: float
    nonreg_real_return: float
    real_estate_appreciation: float
    real_estate_sale_age: int
    cpp_start_age: int
    oas_start_age: int
    
    # Year-by-year results
    yearly_data: List[dict]  # [{year, age, rrsp, tfsa, nonreg, re, total, spending, taxes, ...}]
    
    # Summary
    money_lasts_to_age: Optional[int]
    final_balance: float
    warnings: List[str]


class BatchRetirementPlanOutput(BaseModel):
    """Output model for batch calculations."""
    total_scenarios: int
    scenarios: List[ScenarioResult]
    csv_content: Optional[str] = None  # For download
