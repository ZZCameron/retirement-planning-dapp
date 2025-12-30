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
    PensionIncome,
    TaxCalculationMode
)

from backend.models.canadian_rules import canadian_rules

from backend.models.tax_calculator import calculate_canadian_tax

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

    def _calculate_taxes(self, taxable_income: float, plan_input: 'RetirementPlanInput') -> float:
        """
        Calculate income taxes based on selected calculation mode.
        
        Args:
            taxable_income: Annual taxable income (excludes TFSA withdrawals)
            plan_input: RetirementPlanInput with tax_calculation_mode and province
            
        Returns:
            Total tax owing (federal + provincial)
        """
        if plan_input.tax_calculation_mode == TaxCalculationMode.SIMPLIFIED:
            # Free tier: Simple 25% flat rate approximation
            # Fast but less accurate - good for quick estimates
            return taxable_income * 0.25
        else:
            # Premium tier: Accurate provincial tax calculation
            # Uses 2024 federal and provincial tax brackets with BPA credits
            province = plan_input.province
            if taxable_income <= 0:
                return 0.0
            
            tax_result = calculate_canadian_tax(taxable_income, province)
            return tax_result['total_tax']
    
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
            inflation_factor = 1.0  # Real $ mode: constant purchasing power
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
                rrsp_balance *= (1 + plan_input.rrsp_real_return)
                tfsa_balance *= (1 + plan_input.tfsa_real_return)
                non_reg_balance *= (1 + plan_input.non_reg_real_return)

                
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
                # Subtract mandatory RRIF withdrawal from balance before calculating additional needs
                rrsp_balance -= rrif_withdrawal
                
                # Calculate government benefits
                cpp_income = 0.0
                if current_age >= plan_input.cpp_start_age:
                    cpp_income = adjusted_cpp * 12  # Annual amount
                
                # Calculate pension income from all pensions
                pension_income = 0.0
                for pension in plan_input.pensions:
                    # Calculate year from current_age
                    projection_year = pension.start_year + (current_age - plan_input.current_age)
                    pension_amount = self._calculate_pension_for_year(
                        projection_year,
                        pension,
                        pension.start_year
                    )
                    pension_income += pension_amount
                
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
                
                # STEP 1: Cover spending needs FIRST (before calculating taxes)
                other_withdrawals = 0.0
                rrsp_additional_withdrawal = 0.0  # Track taxable RRSP withdrawals
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
                        
                    # Finally, withdraw from RRSP/RRIF if still short
                    # (Note: This is in addition to any mandatory RRIF minimum withdrawal)
                    if shortfall > 0:
                        rrsp_additional_withdrawal = min(shortfall, rrsp_balance)
                        rrsp_balance -= rrsp_additional_withdrawal
                        rrif_withdrawal += rrsp_additional_withdrawal  # Add to total RRIF withdrawal
                        other_withdrawals += rrsp_additional_withdrawal
                        shortfall -= rrsp_additional_withdrawal

                    # Warning if STILL short after all withdrawals
                    if shortfall > 100:
                        warnings.append(
                            f"Year {year} (age {current_age}): "
                            f"Insufficient funds - shortfall of ${shortfall:,.0f}"
                        )
                
                # STEP 2: Now calculate taxes on taxable income
                # Include: RRIF mandatory withdrawal, CPP, OAS, pension, AND any additional RRSP withdrawals
                taxable_income = gross_income + rrsp_additional_withdrawal  # RRIF, CPP, OAS, pension, and additional RRSP withdrawals are taxable
                # Note: TFSA withdrawals are NOT taxable, non-reg simplified as already taxed
                taxes_estimated = self._calculate_taxes(taxable_income, plan_input)
                
                # STEP 3: Check if we need MORE withdrawals to cover the tax bill
                if taxes_estimated > 0:
                    # Withdraw MORE from TFSA to cover taxes (tax-free withdrawal)
                    tax_coverage_needed = taxes_estimated

                    if tfsa_balance > 0:
                        tfsa_tax_withdrawal = min(tax_coverage_needed, tfsa_balance)
                        tfsa_balance -= tfsa_tax_withdrawal
                        other_withdrawals += tfsa_tax_withdrawal
                        tax_coverage_needed -= tfsa_tax_withdrawal
                    
                    # If TFSA depleted, withdraw from non-registered for remaining taxes
                    if tax_coverage_needed > 0 and non_reg_balance > 0:
                        non_reg_tax_withdrawal = min(tax_coverage_needed, non_reg_balance)
                        non_reg_balance -= non_reg_tax_withdrawal
                        other_withdrawals += non_reg_tax_withdrawal
                        tax_coverage_needed -= non_reg_tax_withdrawal
                    
                    # Tax shortfall already covered by general "Insufficient funds" warning below
                
                # Calculate net income after taxes
                net_income = gross_income + other_withdrawals - taxes_estimated
                             
                # Apply investment returns on remaining balances
                rrsp_balance *= (1 + plan_input.rrsp_real_return)
                tfsa_balance *= (1 + plan_input.tfsa_real_return)
                non_reg_balance *= (1 + plan_input.non_reg_real_return)

                # Real estate sales (handle multiple properties)
                for property in plan_input.real_estate_holdings:
                    if property.sale_age > 0 and current_age == property.sale_age:
                        years_held = current_age - plan_input.current_age
                        sale_value = (property.value * 
                                     (1 + property.real_return) ** years_held)
                        non_reg_balance += sale_value
                        property_label = property.property_type.replace('_', ' ').title()
                        msg = f"{property_label} sold at age {current_age}: +${sale_value:,.0f} (in today's dollars)"
                        warnings.append(msg)

                # Create projection for this year
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
