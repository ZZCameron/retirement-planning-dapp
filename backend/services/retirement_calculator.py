"""
Core retirement planning calculation service.
Implements Canadian retirement rules and projections.
"""

from typing import List, Optional
import logging

from backend.models.retirement_plan import (
    RetirementPlanInput,
    RetirementPlanOutput,
    YearlyProjection,
    PensionIncome
)

from backend.models.canadian_rules import canadian_rules

logger = logging.getLogger(__name__)

class RetirementCalculator:
    """
    Retirement planning calculator for Canadian rules.
    
    This class performs year-by-year projections of retirement finances,
    including RRSP/RRIF, TFSA, government benefits, and withdrawals.
    """
    
    def __init__(self):
        """Initialize calculator with Canadian rules."""
        self.rules = canadian_rules
    
    def calculate_plan(self, plan_input: RetirementPlanInput) -> RetirementPlanOutput:
        """
        Calculate complete retirement plan projection.
        
        Args:
            plan_input: Validated retirement plan parameters
            
        Returns:
            Complete projection with yearly details
        """
        logger.info(f"Calculating retirement plan for age {plan_input.current_age}")
        
        # Calculate timeline
        years_to_retirement = plan_input.retirement_age - plan_input.current_age
        retirement_duration = plan_input.life_expectancy - plan_input.retirement_age
        total_years = plan_input.life_expectancy - plan_input.current_age
        
        # Initialize tracking variables
        projections: List[YearlyProjection] = []
        warnings: List[str] = []
        recommendations: List[str] = []
        
        # Starting balances
        rrsp_balance = plan_input.rrsp_balance
        tfsa_balance = plan_input.tfsa_balance
        non_reg_balance = plan_input.non_registered
        
        # Track contributions
        total_contributions = 0.0
        
        # Adjusted CPP based on start age
        adjusted_cpp = self.rules.calculate_cpp_adjustment(
            plan_input.cpp_start_age,
            plan_input.cpp_monthly
        )
        
        # Year-by-year projection
        for year in range(total_years + 1):
            current_age = plan_input.current_age + year
            is_retired = current_age >= plan_input.retirement_age
            
            # Calculate inflation-adjusted spending
            inflation_factor = (1 + plan_input.expected_inflation) ** year
            adjusted_spending = plan_input.desired_annual_spending * inflation_factor
            
            # ======================
            # ACCUMULATION PHASE
            # ======================
            if not is_retired:
                # Add contributions
                annual_contribution = plan_input.monthly_contribution * 12
                
                # Split contributions (simplified: 70% RRSP, 30% TFSA)
                rrsp_contribution = annual_contribution * 0.70
                tfsa_contribution = annual_contribution * 0.30
                
                rrsp_balance += rrsp_contribution
                tfsa_balance += tfsa_contribution
                total_contributions += annual_contribution
                
                # Apply investment returns
                rrsp_balance *= (1 + plan_input.expected_return)
                tfsa_balance *= (1 + plan_input.expected_return)
                non_reg_balance *= (1 + plan_input.expected_return)
                
                # No withdrawals or benefits during accumulation
                projection = YearlyProjection(
                    year=year,
                    age=current_age,
                    rrsp_rrif_balance=rrsp_balance,
                    tfsa_balance=tfsa_balance,
                    non_registered_balance=non_reg_balance,
                    total_balance=rrsp_balance + tfsa_balance + non_reg_balance,
                    rrif_withdrawal=0.0,
                    cpp_income=0.0,
                    oas_income=0.0,
                    other_withdrawals=0.0,
                    gross_income=0.0,
                    taxes_estimated=0.0,
                    net_income=0.0,
                    spending=0.0
                )
            
            # ======================
            # RETIREMENT PHASE
            # ======================
            else:
                # Calculate RRIF minimum withdrawal (if age 72+)
                rrif_withdrawal = 0.0
                if current_age >= self.rules.RRIF_MINIMUM_START_AGE:
                    # Special case: Age 100 - must withdraw 100% (RRIF closes)
                    if current_age >= 100:
                        rrif_withdrawal = rrsp_balance  # Full withdrawal
                    else:
                        # Use spouse age if provided and younger
                        withdrawal_age = current_age
                        if plan_input.has_spouse and plan_input.spouse_age:
                            spouse_current_age = plan_input.spouse_age + (current_age - plan_input.current_age)
                            withdrawal_age = min(current_age, spouse_current_age)
                        
                        rrif_withdrawal = self.rules.calculate_rrif_minimum_withdrawal(
                            rrsp_balance, 
                            withdrawal_age
                        )
                
                # Calculate government benefits
                cpp_income = 0.0
                if current_age >= plan_input.cpp_start_age:
                    cpp_income = adjusted_cpp * 12  # Annual amount
                
                # Calculate pension income (NEW!)
                pension_income = 0.0
                if plan_input.pension:
                    # Calculate year from current_age
                    projection_year = plan_input.pension.start_year + (current_age - plan_input.current_age)
                    pension_income = self._calculate_pension_for_year(
                        projection_year,
                        plan_input.pension,
                        plan_input.pension.start_year
                    )
                
                oas_income = 0.0
                if current_age >= plan_input.oas_start_age:
                    # Base OAS amount
                    monthly_oas = self.rules.OAS_MAX_MONTHLY_2024
                    if current_age >= 75:
                        monthly_oas = self.rules.OAS_MAX_MONTHLY_75_PLUS
                    
                    annual_oas = monthly_oas * 12
                    
                    # Calculate income for OAS clawback (rough estimate)
                    estimated_income = rrif_withdrawal + cpp_income + pension_income
                    clawback = self.rules.calculate_oas_clawback(estimated_income, current_age)
                    oas_income = max(0, annual_oas - clawback)
                
                # Calculate total income from all sources
                gross_income = rrif_withdrawal + cpp_income + oas_income + pension_income
                
                # Determine additional withdrawals needed
                other_withdrawals = 0.0
                if gross_income < adjusted_spending:
                    shortfall = adjusted_spending - gross_income
                    
                    # Withdraw from TFSA first (tax-free)
                    tfsa_withdrawal = min(shortfall, tfsa_balance)
                    tfsa_balance -= tfsa_withdrawal
                    other_withdrawals += tfsa_withdrawal
                    shortfall -= tfsa_withdrawal
                    
                    # Then from non-registered if needed
                    if shortfall > 0:
                        non_reg_withdrawal = min(shortfall, non_reg_balance)
                        non_reg_balance -= non_reg_withdrawal
                        other_withdrawals += non_reg_withdrawal
                        shortfall -= non_reg_withdrawal
                    
                    # Warning if still short
                    if shortfall > 100:  # Allow small rounding
                        warnings.append(
                            f"Year {year} (age {current_age}): "
                            f"Insufficient funds - shortfall of ${shortfall:,.0f}"
                        )
                
                # Estimate taxes (simplified: ~25% effective rate on taxable income)
                # RRIF, CPP, OAS, and Pension are taxable; TFSA is not
                taxable_income = rrif_withdrawal + cpp_income + oas_income + pension_income
                taxes_estimated = taxable_income * 0.25
                
                # Net income after taxes
                net_income = gross_income + other_withdrawals - taxes_estimated
                
                # Update RRSP/RRIF balance after withdrawal
                rrsp_balance -= rrif_withdrawal
                
                # Apply investment returns on remaining balances
                rrsp_balance *= (1 + plan_input.expected_return)
                tfsa_balance *= (1 + plan_input.expected_return)
                non_reg_balance *= (1 + plan_input.expected_return)
                
                projection = YearlyProjection(
                    year=year,
                    age=current_age,
                    rrsp_rrif_balance=rrsp_balance,
                    tfsa_balance=tfsa_balance,
                    non_registered_balance=non_reg_balance,
                    total_balance=rrsp_balance + tfsa_balance + non_reg_balance,
                    rrif_withdrawal=rrif_withdrawal,
                    cpp_income=cpp_income,
                    oas_income=oas_income,
                    other_withdrawals=other_withdrawals,
                    gross_income=gross_income,
                    taxes_estimated=taxes_estimated,
                    net_income=net_income,
                    spending=adjusted_spending
                )
            
            projections.append(projection)
        
        # Generate recommendations
        final_balance = projections[-1].total_balance
        
        if final_balance < 0:
            recommendations.append(
                "⚠️ Plan runs out of money before life expectancy. "
                "Consider: reducing spending, increasing contributions, or working longer."
            )
        elif final_balance < 50000:
            recommendations.append(
                "⚠️ Very low final balance. Consider building more buffer."
            )
        elif final_balance > 1000000:
            recommendations.append(
                "✅ Strong financial position. Consider legacy planning or increased spending."
            )
        else:
            recommendations.append(
                "✅ Plan appears sustainable with reasonable final balance."
            )
        
        # Check RRIF conversion
        if plan_input.current_age <= 71 and plan_input.retirement_age <= 71:
            recommendations.append(
                f"📋 Remember: RRSP must be converted to RRIF by December 31 of year you turn 71."
            )
        
        # CPP timing recommendation
        if plan_input.cpp_start_age < 65:
            recommendations.append(
                f"💡 Taking CPP at {plan_input.cpp_start_age} reduces benefits. "
                f"Consider delaying if financially viable."
            )
        elif plan_input.cpp_start_age > 65:
            recommendations.append(
                f"✅ Delaying CPP to {plan_input.cpp_start_age} increases benefits by "
                f"{((plan_input.cpp_start_age - 65) * 12 * 0.7):.1f}%"
            )
        
        success = final_balance >= 0 and len(warnings) == 0
        
        return RetirementPlanOutput(
            input_summary=plan_input,
            years_to_retirement=years_to_retirement,
            retirement_duration=retirement_duration,
            total_years=total_years,
            projections=projections,
            total_contributions=total_contributions,
            final_balance=final_balance,
            success=success,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def _calculate_pension_for_year(
        self,
        year: int,
        pension: Optional['PensionIncome'],
        current_year: int
    ) -> float:
        """
        Calculate indexed pension amount for a specific year.
        
        Pension indexing compounds annually from start_year forward.
        For current pensions, start_year should be current year.
        
        Args:
            year: The projection year to calculate
            pension: Optional pension income configuration
            current_year: Current calendar year (e.g., 2024)
            
        Returns:
            Annual pension amount for the year (0 if not applicable)
        """
        if not pension:
            return 0.0
        
        # Pension hasn't started yet
        if year < pension.start_year:
            return 0.0
        
        # Pension has ended
        if pension.end_year and year > pension.end_year:
            return 0.0
        
        # Calculate compound indexing from start year
        years_indexed = year - pension.start_year
        indexed_monthly = pension.monthly_amount * ((1 + pension.indexing_rate) ** years_indexed)
        
        return indexed_monthly * 12  # Return annual amount

# Singleton instance
calculator = RetirementCalculator()
