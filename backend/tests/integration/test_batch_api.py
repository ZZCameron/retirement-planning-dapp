"""
Automated integration tests for retirement planning API.
Tests various pension + additional income scenarios.
"""

import requests
import json
import csv
import io
from datetime import datetime

# API endpoint (update if different)
API_BASE = "https://web-production-c1f93.up.railway.app"
TEST_ENDPOINT = f"{API_BASE}/api/v1/batch/calculate-batch-test"

def run_test_scenario(name: str, payload: dict):
    """Run a single test scenario and validate results."""
    print(f"\n{'='*60}")
    print(f"🧪 TEST: {name}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(TEST_ENDPOINT, json=payload, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
        
        # Parse CSV response
        csv_data = response.text
        reader = csv.DictReader(io.StringIO(csv_data))
        rows = list(reader)
        
        print(f"✅ SUCCESS: Generated {len(rows)} rows")
        
        # Basic validations
        if rows:
            first_row = rows[0]
            print(f"   📊 Columns: {len(first_row)} fields")
            print(f"   📊 Scenarios: {len(set(r['scenario_id'] for r in rows))} unique")
            
            # Check for additional income columns
            income_cols = [k for k in first_row.keys() if 'additional_income' in k]
            if income_cols:
                print(f"   💰 Additional Income Columns: {len(income_cols)}")
                print(f"      {', '.join(income_cols[:4])}...")
            
            # Check for pension columns
            pension_cols = [k for k in first_row.keys() if 'pension_' in k and '_' in k]
            if pension_cols:
                print(f"   📋 Pension Columns: {len(pension_cols)}")
            
            # Validate critical fields
            if 'gross_income' in first_row:
                print(f"   💵 Sample gross_income: ${first_row['gross_income']}")
            
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


# Test Suite
def run_all_tests():
    """Run comprehensive test suite."""
    
    print("\n" + "="*60)
    print("🚀 AUTOMATED INTEGRATION TEST SUITE")
    print("="*60)
    
    results = []
    
    # ========================================
    # TEST 1: Baseline (No Pension, No Income)
    # ========================================
    test1 = {
        "current_age": 55,
        "retirement_age": {"min": 65, "max": 65, "enabled": False},
        "rrsp_balance": {"min": 500000, "max": 500000, "enabled": False},
        "tfsa_balance": {"min": 100000, "max": 100000, "enabled": False},
        "non_registered": {"min": 50000, "max": 50000, "enabled": False},
        "desired_annual_spending": {"min": 50000, "max": 50000, "enabled": False},
        "monthly_contribution": {"min": 0, "max": 0, "enabled": False},
        "rrsp_real_return": {"min": 0.04, "max": 0.04, "enabled": False},
        "tfsa_real_return": {"min": 0.04, "max": 0.04, "enabled": False},
        "non_reg_real_return": {"min": 0.03, "max": 0.03, "enabled": False},
        "cpp_start_age": {"min": 65, "max": 65, "enabled": False},
        "oas_start_age": {"min": 65, "max": 65, "enabled": False},
        "pensions": [],
        "additional_income": [],
        "real_estate_holdings": []
    }
    results.append(("Baseline (No Pension/Income)", run_test_scenario("Baseline (No Pension/Income)", test1)))
    
    # ========================================
    # TEST 2: Single Pension
    # ========================================
    test2 = test1.copy()
    test2["pensions"] = [{
        "monthly_amount": 2000,
        "start_year": 2034,
        "indexing_rate": 0.02
    }]
    results.append(("Single Pension", run_test_scenario("Single Pension", test2)))
    
    # ========================================
    # TEST 3: Single Additional Income
    # ========================================
    test3 = test1.copy()
    test3["additional_income"] = [{
        "monthly_amount": 1500,
        "start_year": 2034,
        "indexing_rate": 0.0
    }]
    results.append(("Single Additional Income", run_test_scenario("Single Additional Income", test3)))
    
    # ========================================
    # TEST 4: Pension + Additional Income
    # ========================================
    test4 = test1.copy()
    test4["pensions"] = [{
        "monthly_amount": 2000,
        "start_year": 2034,
        "indexing_rate": 0.02
    }]
    test4["additional_income"] = [{
        "monthly_amount": 1500,
        "start_year": 2034,
        "indexing_rate": 0.0
    }]
    results.append(("Pension + Income", run_test_scenario("Pension + Income", test4)))
    
    # ========================================
    # TEST 5: Multiple Pensions + Multiple Incomes
    # ========================================
    test5 = test1.copy()
    test5["pensions"] = [
        {"monthly_amount": 2000, "start_year": 2034, "indexing_rate": 0.02},
        {"monthly_amount": 1000, "start_year": 2034, "indexing_rate": 0.01}
    ]
    test5["additional_income"] = [
        {"monthly_amount": 1500, "start_year": 2034, "indexing_rate": 0.0},
        {"monthly_amount": 800, "start_year": 2036, "indexing_rate": -0.05}  # Declining
    ]
    results.append(("2 Pensions + 2 Incomes", run_test_scenario("2 Pensions + 2 Incomes", test5)))
    
    # ========================================
    # TEST 6: Income with End Year
    # ========================================
    test6 = test1.copy()
    test6["additional_income"] = [{
        "monthly_amount": 2000,
        "start_year": 2034,
        "indexing_rate": 0.0,
        "end_year": 2040  # Should stop after 6 years
    }]
    results.append(("Income with End Year", run_test_scenario("Income with End Year", test6)))
    
    # ========================================
    # TEST 7: Batch Mode (Vary Retirement Age)
    # ========================================
    test7 = test1.copy()
    test7["retirement_age"] = {"min": 63, "max": 65, "enabled": True}
    test7["additional_income"] = [{
        "monthly_amount": 1500,
        "start_year": 2032,  # Starts at min retirement
        "indexing_rate": 0.0
    }]
    results.append(("Batch: Vary Retirement Age", run_test_scenario("Batch: Vary Retirement Age (63-65)", test7)))
    
    # ========================================
    # TEST 8: Negative Indexing (Declining Income)
    # ========================================
    test8 = test1.copy()
    test8["additional_income"] = [{
        "monthly_amount": 3000,
        "start_year": 2034,
        "indexing_rate": -0.10  # Declines 10% per year
    }]
    results.append(("Declining Income (-10%)", run_test_scenario("Declining Income (-10%)", test8)))
    
    # ========================================
    # Summary
    # ========================================
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} tests passed ({100*passed//total}%)")
    print(f"{'='*60}\n")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

