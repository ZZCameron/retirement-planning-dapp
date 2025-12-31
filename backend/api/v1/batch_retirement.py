# Updated for pension/property arrays
"""
Batch retirement planning API endpoint.
Handles bulk scenario calculations with payment verification.
"""
import logging
import io
import csv
from typing import List
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from backend.config import settings
from backend.models.batch_retirement_plan import (
    BatchRetirementPlanInput,
    BatchRetirementPlanOutput,
    ScenarioResult
)
from backend.services.scenario_generator import (
    ScenarioGenerator,
    validate_batch_feasibility
)
from backend.services.retirement_calculator import RetirementCalculator
from backend.services.payment_verifier import SolanaPaymentVerifier

logger = logging.getLogger(__name__)

router = APIRouter()

# Pricing configuration
SOL_PER_RUN = 0.00002  # 0.00002 SOL per scenario (~$0.002-0.004 USD)


@router.post("/calculate-batch-estimate")
async def estimate_batch_calculation(
    batch_input: BatchRetirementPlanInput
) -> dict:
    """
    Estimate cost and time for batch calculation (no payment required).
    
    Returns scenario count, estimated time, and cost in SOL.
    """
    # Validate feasibility
    validation = validate_batch_feasibility(batch_input)
    
    if not validation['feasible']:
        raise HTTPException(
            status_code=400,
            detail=validation['error']
        )
    
    # Calculate cost
    scenario_count = validation['scenario_count']
    cost_sol = scenario_count * SOL_PER_RUN
    
    return {
        "scenario_count": scenario_count,
        "enabled_fields": validation['enabled_fields'],
        "estimated_time_seconds": validation['estimated_time_seconds'],
        "cost_sol": cost_sol,
        "cost_usd_estimate": cost_sol * 150,  # Rough estimate at $150/SOL
        "feasible": True
    }


@router.post("/calculate-batch")
async def calculate_batch_scenarios(
    batch_input: BatchRetirementPlanInput,
    payment_signature: str = Query(..., description="Solana transaction signature"),
    wallet_address: str = Query(..., description="User's wallet address"),
):
    """
    Calculate retirement scenarios with payment verification.
    Returns CSV file with all scenario results.
    """
    logger.info(f"Batch calculation request from wallet {wallet_address[:8]}...")
    
    # 1. Validate feasibility
    validation = validate_batch_feasibility(batch_input)
    if not validation['feasible']:
        raise HTTPException(
            status_code=400,
            detail=f"Batch not feasible: {validation['error']}"
        )
    
    scenario_count = validation['scenario_count']
    logger.info(f"Processing {scenario_count} scenarios ({validation['enabled_fields']} enabled fields)")
    
    # 2. Verify payment
    expected_payment_sol = scenario_count * SOL_PER_RUN
    
    verifier = SolanaPaymentVerifier(
        rpc_url=settings.solana_rpc_url,
        expected_recipient=settings.treasury_wallet,
        expected_amount_sol=expected_payment_sol,
    )
    
    verification = await verifier.verify_transaction(payment_signature, wallet_address)
    
    if not verification.verified:
        raise HTTPException(
            status_code=402,  # Payment Required
            detail=f"Payment verification failed: {verification.error}"
        )
    
    logger.info(f"✅ Payment verified: {verification.amount_sol} SOL (tx: {payment_signature[:8]}...)")
    
    # 3. Generate scenarios
    generator = ScenarioGenerator(batch_input)
    scenarios = generator.generate_scenarios()
    
    logger.info(f"Generated {len(scenarios)} scenario combinations")
    
    # 4. Calculate all scenarios
    calculator = RetirementCalculator()
    results = []
    
    for i, scenario_input in enumerate(scenarios, start=1):
        if i % 100 == 0:
            logger.info(f"Processing scenario {i}/{len(scenarios)}...")
        
        try:
            result = calculator.calculate_plan(scenario_input)
            results.append({
                'scenario_id': i,
                'input': scenario_input,
                'output': result
            })
        except Exception as e:
            logger.error(f"Error calculating scenario {i}: {e}")
            # Continue with other scenarios
            results.append({
                'scenario_id': i,
                'input': scenario_input,
                'error': str(e)
            })
    
    logger.info(f"✅ Completed {len(results)} calculations")
    
    # 5. Format as CSV
    csv_content = format_results_as_csv(results, batch_input)
    
    # 6. Return as downloadable file
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=retirement_scenarios_{payment_signature[:8]}.csv"
        }
    )


def format_results_as_csv(results: List[dict], batch_input: BatchRetirementPlanInput) -> str:
    """
    Format scenario results as CSV with year-by-year data.
    
    CSV structure:
    scenario_id, retirement_age, rrsp_balance, ..., year, age, rrsp, tfsa, nonreg, total, taxes, warnings
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    header = [
        'scenario_id',
        # Input parameters
        'retirement_age', 'rrsp_balance', 'tfsa_balance', 'nonreg_balance',
        'annual_spending', 'monthly_savings',
        'rrsp_real_return', 'tfsa_real_return', 'nonreg_real_return',
        'real_estate_appreciation', 'real_estate_sale_age',
        'cpp_start_age', 'oas_start_age',
        # Year-by-year data
        'year', 'age',
        'rrsp_rrif_balance', 'tfsa_balance_eoy', 'nonreg_balance_eoy',
        'total_balance', 'gross_income', 'taxes_estimated',
        'success', 'final_balance', 'warnings'
    ]
    writer.writerow(header)
    
    # Data rows (one per scenario per year)
    for result in results:
        scenario_id = result['scenario_id']
        scenario_input = result['input']
        
        if 'error' in result:
            # Write error row
            row = [scenario_id] + ['ERROR'] * (len(header) - 1)
            writer.writerow(row)
            continue
        
        scenario_output = result['output']
        
        # Extract input parameters
        input_params = [
            scenario_input.retirement_age,
            scenario_input.rrsp_balance,
            scenario_input.tfsa_balance,
            scenario_input.non_registered,
            scenario_input.desired_annual_spending,
            scenario_input.monthly_contribution,
            scenario_input.rrsp_real_return,
            scenario_input.tfsa_real_return,
            scenario_input.non_reg_real_return,
            scenario_input.real_estate_real_return,
            scenario_input.real_estate_sale_age,
            scenario_input.cpp_start_age,
            scenario_input.oas_start_age,
        ]
        
        # Summary data
        final_balance = scenario_output.final_balance
        success = scenario_output.success
        warnings_str = "; ".join(scenario_output.warnings) if scenario_output.warnings else ""
        
        # Write one row per year (using correct field names)
        for projection in scenario_output.projections:
            row = [scenario_id] + input_params + [
                projection.year,
                projection.age,
                projection.rrsp_rrif_balance,
                projection.tfsa_balance,
                projection.non_registered_balance,
                projection.total_balance,
                projection.gross_income,
                projection.taxes_estimated,
                success,
                final_balance,
                warnings_str
            ]
            writer.writerow(row)
    
    return output.getvalue()


@router.post("/calculate-batch-test")
async def calculate_batch_test(
    batch_input: BatchRetirementPlanInput
):
    """
    TEST ONLY: Calculate batch without payment verification.
    Remove this endpoint before production deployment!
    """
    logger.warning("⚠️ Using TEST endpoint - no payment verification!")
    
    # Validate feasibility
    validation = validate_batch_feasibility(batch_input)
    if not validation['feasible']:
        raise HTTPException(status_code=400, detail=validation['error'])
    
    # Generate scenarios
    generator = ScenarioGenerator(batch_input)
    scenarios = generator.generate_scenarios()
    
    logger.info(f"Calculating {len(scenarios)} scenarios...")
    
    # Calculate all scenarios
    calculator = RetirementCalculator()
    results = []
    
    for i, scenario_input in enumerate(scenarios, start=1):
        try:
            result = calculator.calculate_plan(scenario_input)
            results.append({
                'scenario_id': i,
                'input': scenario_input,
                'output': result
            })
        except Exception as e:
            logger.error(f"Error in scenario {i}: {e}")
            results.append({
                'scenario_id': i,
                'input': scenario_input,
                'error': str(e)
            })
    
    # Format as CSV
    csv_content = format_results_as_csv(results, batch_input)
    
    # Return as file
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=test_scenarios.csv"}
    )
