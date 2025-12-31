"""
Scenario generator for batch retirement calculations.
Generates all combinations of enabled range fields.
"""
import logging
from typing import List, Dict, Any
from itertools import product

from backend.models.batch_retirement_plan import (
    BatchRetirementPlanInput,
    RangeField,
    ScenarioResult
)
from backend.models.retirement_plan import RetirementPlanInput

logger = logging.getLogger(__name__)


class ScenarioGenerator:
    """Generates all scenario combinations from batch input."""
    
    def __init__(self, batch_input: BatchRetirementPlanInput):
        self.batch_input = batch_input
        self.enabled_count = batch_input.count_enabled_fields()
        self.scenario_count = batch_input.estimate_scenario_count()
    
    def generate_scenarios(self) -> List[RetirementPlanInput]:
        """
        Generate all scenario combinations.
        
        Returns:
            List of RetirementPlanInput objects ready for calculator
        """
        logger.info(f"Generating {self.scenario_count} scenarios ({self.enabled_count} enabled fields)")
        
        # Get all value combinations for enabled fields
        field_values = self._get_field_value_combinations()
        
        # Generate individual scenarios
        scenarios = []
        for scenario_id, values in enumerate(field_values, start=1):
            scenario = self._create_scenario(scenario_id, values)
            scenarios.append(scenario)
        
        logger.info(f"✅ Generated {len(scenarios)} scenarios")
        return scenarios
    
    def _get_field_value_combinations(self) -> List[Dict[str, Any]]:
        """
        Generate all combinations of field values.
        
        Returns:
            List of dicts with field values for each scenario
        """
        # Extract values for each field
        fields = {
            'retirement_age': self.batch_input.retirement_age.get_values(),
            'rrsp_balance': self.batch_input.rrsp_balance.get_values(),
            'tfsa_balance': self.batch_input.tfsa_balance.get_values(),
            'nonreg_balance': self.batch_input.nonreg_balance.get_values(),
            'annual_spending': self.batch_input.annual_spending.get_values(),
            'monthly_savings': self.batch_input.monthly_savings.get_values(),
            'rrsp_real_return': self.batch_input.rrsp_real_return.get_values(),
            'tfsa_real_return': self.batch_input.tfsa_real_return.get_values(),
            'nonreg_real_return': self.batch_input.nonreg_real_return.get_values(),
            # real_estate_holdings passed directly as list (not in combinations)
            'cpp_start_age': self.batch_input.cpp_start_age.get_values(),
            'oas_start_age': self.batch_input.oas_start_age.get_values(),
        }
        
        # Generate all combinations using itertools.product
        field_names = list(fields.keys())
        value_lists = [fields[name] for name in field_names]
        
        combinations = []
        for combo in product(*value_lists):
            scenario_values = dict(zip(field_names, combo))
            combinations.append(scenario_values)
        
        return combinations
    
    def _create_scenario(self, scenario_id: int, values: Dict[str, Any]) -> RetirementPlanInput:
        """
        Create a single RetirementPlanInput from scenario values.
        
        Args:
            scenario_id: Unique identifier for this scenario
            values: Dict of field values for this scenario
            
        Returns:
            RetirementPlanInput object
        """
        # Pass through the list of pensions directly
        # (No need to process - calculator handles the list)
        
        # Build RetirementPlanInput (matches existing calculator format)
        scenario = RetirementPlanInput(
            current_age=self.batch_input.current_age,
            retirement_age=int(values['retirement_age']),
            life_expectancy=self.batch_input.life_expectancy,
            province=self.batch_input.province,  # Full name expected (e.g., "Ontario")
            
            # Account balances (correct field names)
            rrsp_balance=values['rrsp_balance'],
            tfsa_balance=values['tfsa_balance'],
            non_registered=values['nonreg_balance'],  # Note: non_registered, not non_registered_balance
            
            # Contributions & spending (correct field names)
            monthly_contribution=values['monthly_savings'],  # Note: monthly_contribution
            desired_annual_spending=values['annual_spending'],  # Note: desired_annual_spending
            
            # Real returns (correct field names)
            rrsp_real_return=values['rrsp_real_return'],
            tfsa_real_return=values['tfsa_real_return'],
            non_reg_real_return=values['nonreg_real_return'],  # Note: non_reg_real_return
            
            # Real estate (correct field names)
            real_estate_holdings=[p.model_dump() for p in self.batch_input.real_estate_holdings],  # Convert to dicts
            
            # Government benefits (need cpp_monthly - use default)
            cpp_monthly=1200.0,  # Default CPP benefit at 65
            cpp_start_age=int(values['cpp_start_age']),
            oas_start_age=int(values['oas_start_age']),
            
            # Pension (correct field name)
            pensions=[p.model_dump() for p in self.batch_input.pensions],  # Convert to dicts
        )
        
        return scenario


def estimate_processing_time(scenario_count: int) -> float:
    """
    Estimate processing time in seconds.
    
    Args:
        scenario_count: Number of scenarios to calculate
        
    Returns:
        Estimated time in seconds (conservative)
    """
    MS_PER_SCENARIO = 40  # Conservative average
    SAFETY_MARGIN = 1.5   # 50% buffer
    
    estimated_ms = scenario_count * MS_PER_SCENARIO * SAFETY_MARGIN
    return estimated_ms / 1000  # Convert to seconds


def validate_batch_feasibility(batch_input: BatchRetirementPlanInput) -> Dict[str, Any]:
    """
    Validate if batch is feasible within time/resource limits.
    
    Args:
        batch_input: Batch input to validate
        
    Returns:
        Dict with validation results:
        {
            'feasible': bool,
            'scenario_count': int,
            'estimated_time_seconds': float,
            'enabled_fields': int,
            'error': str or None
        }
    """
    enabled_fields = batch_input.count_enabled_fields()
    scenario_count = batch_input.estimate_scenario_count()
    estimated_time = estimate_processing_time(scenario_count)
    
    # Hard limits
    MAX_SCENARIOS = 4096  # 2^12
    MAX_TIME_SECONDS = 480  # 8 minutes (Railway timeout - 2 min buffer)
    MAX_ENABLED_FIELDS = 12
    
    result = {
        'feasible': True,
        'scenario_count': scenario_count,
        'estimated_time_seconds': estimated_time,
        'enabled_fields': enabled_fields,
        'error': None
    }
    
    if enabled_fields > MAX_ENABLED_FIELDS:
        result['feasible'] = False
        result['error'] = f"Too many enabled fields ({enabled_fields}). Maximum: {MAX_ENABLED_FIELDS}"
    elif scenario_count > MAX_SCENARIOS:
        result['feasible'] = False
        result['error'] = f"Too many scenarios ({scenario_count}). Maximum: {MAX_SCENARIOS}"
    elif estimated_time > MAX_TIME_SECONDS:
        result['feasible'] = False
        result['error'] = f"Estimated time ({estimated_time:.0f}s) exceeds maximum ({MAX_TIME_SECONDS}s)"
    
    return result
