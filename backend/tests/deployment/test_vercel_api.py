"""
End-to-end tests for Vercel-deployed API endpoints.

Run with:
    pytest backend/tests/deployment/test_vercel_api.py
    
Or test specific environment:
    VERCEL_URL=https://www.web3-retirement-plan.com pytest backend/tests/deployment/
"""
import os
import pytest
import httpx

# Default to staging
VERCEL_URL = os.getenv(
    "VERCEL_URL",
    "https://retirement-planning-dapp-git-develop-robert-camerons-projects.vercel.app"
)

@pytest.mark.asyncio
async def test_free_calculate():
    """Test free retirement calculation endpoint"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{VERCEL_URL}/api/v1/retirement/calculate",
            json={
                "current_age": 55,
                "retirement_age": 65,
                "life_expectancy": 90,
                "province": "ON",
                "rrsp_balance": {"min": 100000, "max": 100000},
                "tfsa_balance": {"min": 30000, "max": 30000},
                "nonreg_balance": {"min": 0, "max": 0},
                "annual_spending": {"min": 60000, "max": 60000},
                "monthly_savings": {"min": 1500, "max": 1500},
                "rrsp_real_return": {"min": 0.02, "max": 0.02},
                "tfsa_real_return": {"min": 0.04, "max": 0.04},
                "nonreg_real_return": {"min": 0.05, "max": 0.05},
                "real_estate_appreciation": 0.02,
                "real_estate_sale_age": 0,
                "cpp_start_age": {"min": 65, "max": 65},
                "oas_start_age": {"min": 65, "max": 65},
                "pensions": [],
                "additional_income": [],
                "real_estate_holdings": []
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "money_lasts_to_age" in data
        assert "projections" in data
        assert len(data["projections"]) > 0


@pytest.mark.asyncio
async def test_enhanced_estimate():
    """Test enhanced insights cost estimation"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{VERCEL_URL}/api/v1/retirement/calculate-enhanced-estimate",
            json={"current_age": 55, "retirement_age": 65}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "required_payment_sol" in data
        assert data["required_payment_sol"] > 0


@pytest.mark.asyncio
async def test_batch_estimate():
    """Test batch analysis cost estimation"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{VERCEL_URL}/api/v1/batch/calculate-batch-estimate",
            json={
                "current_age": 55,
                "retirement_age": {"min": 65, "max": 67},
                "life_expectancy": 90,
                "province": "ON",
                "rrsp_balance": {"min": 100000, "max": 100000},
                "tfsa_balance": {"min": 30000, "max": 30000},
                "nonreg_balance": {"min": 0, "max": 0},
                "annual_spending": {"min": 60000, "max": 70000},
                "monthly_savings": {"min": 1500, "max": 1500},
                "rrsp_real_return": {"min": 0.02, "max": 0.02},
                "tfsa_real_return": {"min": 0.04, "max": 0.04},
                "nonreg_real_return": {"min": 0.05, "max": 0.05},
                "real_estate_appreciation": 0.02,
                "real_estate_sale_age": 0,
                "cpp_start_age": {"min": 65, "max": 65},
                "oas_start_age": {"min": 65, "max": 65},
                "pensions": [],
                "additional_income": [],
                "real_estate_holdings": []
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "scenario_count" in data
        assert data["scenario_count"] > 0
        assert "required_payment_sol" in data


@pytest.mark.asyncio
async def test_cors_headers():
    """Verify CORS headers are present for API routes"""
    async with httpx.AsyncClient() as client:
        # OPTIONS preflight request
        response = await client.options(
            f"{VERCEL_URL}/api/v1/retirement/calculate",
            headers={"Origin": "https://www.web3-retirement-plan.com"}
        )
        
        assert response.status_code in [200, 204]
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers


if __name__ == "__main__":
    import asyncio
    
    print("🧪 Running Vercel API Tests")
    print(f"Target: {VERCEL_URL}\n")
    
    asyncio.run(test_free_calculate())
    print("✅ Free Calculate")
    
    asyncio.run(test_enhanced_estimate())
    print("✅ Enhanced Estimate")
    
    asyncio.run(test_batch_estimate())
    print("✅ Batch Estimate")
    
    asyncio.run(test_cors_headers())
    print("✅ CORS Headers")
    
    print("\n✅ All tests passed!")
