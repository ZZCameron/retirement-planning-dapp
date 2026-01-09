"""
Fixed integration test with correct BatchRetirementPlanInput structure
"""
import requests
import json

API_BASE = "https://web-production-c1f93.up.railway.app"
TEST_ENDPOINT = f"{API_BASE}/api/v1/batch/calculate-batch-test"

def test_simple_batch():
    """Test with minimal batch input (no variations)"""
    
    payload = {
        # Single-value fields
        "current_age": 60,
        "life_expectancy": 95,
        "province": "Ontario",
        "real_estate_holdings": [],
        "pensions": [],
        "additional_income": [],
        
        # RangeField objects (all disabled = single scenario)
        "retirement_age": {"min": 65, "max": 65, "step": 1, "enabled": False},
        "rrsp_balance": {"min": 500000, "max": 500000, "step": 50000, "enabled": False},
        "tfsa_balance": {"min": 250000, "max": 250000, "step": 50000, "enabled": False},
        "nonreg_balance": {"min": 100000, "max": 100000, "step": 25000, "enabled": False},
        "annual_spending": {"min": 50000, "max": 50000, "step": 5000, "enabled": False},
        "monthly_savings": {"min": 2000, "max": 2000, "step": 500, "enabled": False},
        
        "rrsp_real_return": {"min": 0.05, "max": 0.05, "step": 0.01, "enabled": False},
        "tfsa_real_return": {"min": 0.05, "max": 0.05, "step": 0.01, "enabled": False},
        "nonreg_real_return": {"min": 0.04, "max": 0.04, "step": 0.01, "enabled": False},
        
        "real_estate_appreciation": {"min": 0.03, "max": 0.03, "step": 0.01, "enabled": False},
        "real_estate_sale_age": {"min": 70, "max": 70, "step": 5, "enabled": False},
        
        "cpp_start_age": {"min": 65, "max": 65, "step": 1, "enabled": False},
        "oas_start_age": {"min": 65, "max": 65, "step": 1, "enabled": False}
    }
    
    print("\n🧪 Testing batch endpoint with proper structure...")
    response = requests.post(TEST_ENDPOINT, json=payload, timeout=60)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        # Should return CSV
        lines = response.text.split('\n')
        print(f"✅ SUCCESS - Got {len(lines)} lines of CSV")
        print(f"Header: {lines[0][:100]}...")
        return True
    else:
        print(f"❌ FAILED - {response.text[:200]}")
        return False

if __name__ == "__main__":
    success = test_simple_batch()
    exit(0 if success else 1)
