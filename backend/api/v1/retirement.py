"""
Retirement planning API endpoints.
Version 1.
"""

import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from backend.models.retirement_plan import (
    RetirementPlanInput,
    RetirementPlanOutput,
)
from backend.services.retirement_calculator import calculator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/calculate",
    response_model=RetirementPlanOutput,
    status_code=status.HTTP_200_OK,
    summary="Calculate retirement plan",
    description="Calculate a complete retirement plan projection based on Canadian rules"
)
async def calculate_retirement_plan(
    plan_input: RetirementPlanInput
) -> RetirementPlanOutput:
    """
    Calculate retirement plan projection.
    
    This endpoint:
    - Validates input parameters
    - Applies Canadian retirement rules (RRIF, CPP, OAS)
    - Projects year-by-year financial status
    - Provides warnings and recommendations
    
    **Security Note**: All calculations are stateless and client-side data only.
    No personal information is stored.
    """
    try:
        logger.info(f"Received calculation request for age {plan_input.current_age}")
        
        # Perform calculation
        result = calculator.calculate_plan(plan_input)
        
        logger.info(
            f"Calculation complete: {result.total_years} years projected, "
            f"success={result.success}"
        )
        
        return result
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid input: {str(e)}"
        )
    
    except Exception as e:
        logger.error(f"Calculation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during calculation. Please check your inputs."
        )


@router.get(
    "/rules",
    summary="Get Canadian retirement rules",
    description="Retrieve current Canadian retirement planning rules and constants"
)
async def get_retirement_rules():
    """
    Get Canadian retirement rules and constants.
    
    Returns current rules including:
    - RRSP/RRIF contribution limits
    - CPP/OAS benefit amounts
    - RRIF minimum withdrawal factors
    - Tax withholding rates
    """
    from backend.models.canadian_rules import CanadianRetirementRules
    
    return JSONResponse({
        "year": "2024/2025",
        "rrsp_contribution_limit": CanadianRetirementRules.RRSP_CONTRIBUTION_LIMIT_2024,
        "tfsa_contribution_limit": CanadianRetirementRules.TFSA_CONTRIBUTION_LIMIT_2024,
        "rrsp_conversion_age": CanadianRetirementRules.RRSP_CONVERSION_AGE,
        "rrif_minimum_start_age": CanadianRetirementRules.RRIF_MINIMUM_START_AGE,
        "oas_max_monthly_65_74": CanadianRetirementRules.OAS_MAX_MONTHLY_2024,
        "oas_max_monthly_75_plus": CanadianRetirementRules.OAS_MAX_MONTHLY_75_PLUS,
        "cpp_max_monthly_at_65": CanadianRetirementRules.CPP_MAX_MONTHLY_2024,
        "cpp_age_range": {
            "earliest": CanadianRetirementRules.CPP_EARLIEST_AGE,
            "normal": CanadianRetirementRules.CPP_NORMAL_AGE,
            "latest": CanadianRetirementRules.CPP_LATEST_AGE
        },
        "note": "All amounts in CAD. Rules updated annually."
    })
