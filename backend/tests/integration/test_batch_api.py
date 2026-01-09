"""
Integration tests for batch retirement calculation API
Tests various pension + additional income scenarios
"""
import requests
import json
import csv
import io

API_BASE = "https://web-production-c1f93.up.railway.app"
TEST_ENDPOINT = f"{API_BASE}/api/v1/batch/calculate-batch-test"

def create_base_payload():
    """Create base payload with proper RangeField structure"""
    return {
        "current_age": 60,
        "life_expectancy": 95,
        "province": "Ontario",
        "real_estate_holdings": [],
        "pensions": [],
        "additional_income": [],
        
        # All disabled = single scenario
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

def run_test(name, payload):
    """Run a single test scenario"""
    print(f"\n{'='*60}")
    print(f"🧪 Test: {name}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(TEST_ENDPOINT, json=payload, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ FAILED - HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(response.text))
        rows = list(csv_reader)
        
        # Get unique scenarios
        scenarios = set(row['scenario_id'] for row in rows)
        
        print(f"✅ PASSED")
        print(f"   Scenarios: {len(scenarios)}")
        print(f"   Total rows: {len(rows)}")
        
        # Check for additional_income columns
        if rows:
            has_income_cols = 'num_additional_income' in rows[0]
            print(f"   Has income columns: {has_income_cols}")
            
            if has_income_cols and rows[0]['num_additional_income']:
                print(f"   Additional income streams: {rows[0]['num_additional_income']}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED - {str(e)}")
        return False

def test_baseline():
    """Test 1: Baseline (no pension/income)"""
    payload = create_base_payload()
    return run_test("Baseline (No Pension/Income)", payload)

def test_single_pension():
    """Test 2: Single pension"""
    payload = create_base_payload()
    payload["pensions"] = [{
        "monthly_amount": 3000,
        "start_year": 2034,
        "indexing_rate": 0.02,
        "end_year": None
    }]
    return run_test("Single Pension ($3k/mo)", payload)

def test_single_income():
    """Test 3: Single additional income"""
    payload = create_base_payload()
    payload["additional_income"] = [{
        "monthly_amount": 2500,
        "start_year": 2034,
        "indexing_rate": 0.0,
        "end_year": None
    }]
    return run_test("Single Additional Income ($2.5k/mo)", payload)

def test_pension_and_income():
    """Test 4: Pension + Income"""
    payload = create_base_payload()
    payload["pensions"] = [{
        "monthly_amount": 2000,
        "start_year": 2034,
        "indexing_rate": 0.02,
        "end_year": None
    }]
    payload["additional_income"] = [{
        "monthly_amount": 1500,
        "start_year": 2034,
        "indexing_rate": 0.0,
        "end_year": None
    }]
    return run_test("Pension + Income", payload)

def test_multiple_streams():
    """Test 5: 2 Pensions + 2 Incomes"""
    payload = create_base_payload()
    payload["pensions"] = [
        {"monthly_amount": 2000, "start_year": 2034, "indexing_rate": 0.02, "end_year": None},
        {"monthly_amount": 1500, "start_year": 2034, "indexing_rate": 0.015, "end_year": None}
    ]
    payload["additional_income"] = [
        {"monthly_amount": 3000, "start_year": 2034, "indexing_rate": 0.0, "end_year": None},
        {"monthly_amount": 1000, "start_year": 2037, "indexing_rate": 0.0, "end_year": 2045}
    ]
    return run_test("2 Pensions + 2 Incomes", payload)

def test_income_with_end_year():
    """Test 6: Income with end_year"""
    payload = create_base_payload()
    payload["additional_income"] = [{
        "monthly_amount": 2000,
        "start_year": 2034,
        "indexing_rate": 0.0,
        "end_year": 2038
    }]
    return run_test("Income with End Year (2038)", payload)

def test_batch_vary_retirement():
    """Test 7: Batch mode - vary retirement age"""
    payload = create_base_payload()
    payload["retirement_age"] = {"min": 63, "max": 65, "step": 1, "enabled": True}
    return run_test("Batch: Vary Retirement Age (63-65)", payload)

def test_declining_income():
    """Test 8: Declining income (-10% indexing)"""
    payload = create_base_payload()
    payload["additional_income"] = [{
        "monthly_amount": 3000,
        "start_year": 2034,
        "indexing_rate": -0.10,
        "end_year": None
    }]
    return run_test("Declining Income (-10%)", payload)

def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("🚀 INTEGRATION TEST SUITE: Batch Retirement API")
    print("="*60)
    
    tests = [
        test_baseline,
        test_single_pension,
        test_single_income,
        test_pension_and_income,
        test_multiple_streams,
        test_income_with_end_year,
        test_batch_vary_retirement,
        test_declining_income
    ]
    
    results = [test() for test in tests]
    
    passed = sum(results)
    total = len(results)
    
    print("\n" + "="*60)
    print(f"📊 RESULTS: {passed}/{total} tests passed ({100*passed//total}%)")
    print("="*60)
    
    return all(results)

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
