"""
Test suite for Canadian provincial tax calculator
"""
from backend.models.tax_calculator import calculate_canadian_tax

def test_ontario_taxes():
    """Test Ontario tax calculation"""
    income = 100000
    result = calculate_canadian_tax(income, "Ontario")
    
    print(f"\n=== Ontario Test (Income: ${income:,}) ===")
    print(f"Federal Tax:     ${result['federal_tax']:,.2f}")
    print(f"Provincial Tax:  ${result['provincial_tax']:,.2f}")
    print(f"Total Tax:       ${result['total_tax']:,.2f}")
    print(f"After-Tax:       ${result['after_tax_income']:,.2f}")
    print(f"Effective Rate:  {result['effective_rate']:.2f}%")
    print(f"Marginal Rate:   {result['marginal_rate']:.2f}%")
    
    # Verify reasonable tax amount (roughly 20-25% effective rate)
    assert 20000 < result['total_tax'] < 30000, "Tax amount seems unreasonable"
    assert result['after_tax_income'] == income - result['total_tax']

def test_alberta_taxes():
    """Test Alberta tax calculation (flat 10% rate)"""
    income = 100000
    result = calculate_canadian_tax(income, "Alberta")
    
    print(f"\n=== Alberta Test (Income: ${income:,}) ===")
    print(f"Federal Tax:     ${result['federal_tax']:,.2f}")
    print(f"Provincial Tax:  ${result['provincial_tax']:,.2f}")
    print(f"Total Tax:       ${result['total_tax']:,.2f}")
    print(f"After-Tax:       ${result['after_tax_income']:,.2f}")
    print(f"Effective Rate:  {result['effective_rate']:.2f}%")
    
    # At $100k, Alberta's flat 10% rate results in HIGHER tax than Ontario's graduated rates
    ontario_result = calculate_canadian_tax(income, "Ontario")
    assert result['total_tax'] > ontario_result['total_tax'], \
        f"Alberta tax (${result['total_tax']:,.2f}) should be MORE than Ontario (${ontario_result['total_tax']:,.2f}) at $100k income"
    
    # Verify the difference is approximately $1,765 (Alberta pays more)
    tax_difference = result['total_tax'] - ontario_result['total_tax']
    assert 1700 < tax_difference < 1900, \
        f"Tax difference should be ~$1,765, got ${tax_difference:,.2f}"

def test_bc_taxes():
    """Test British Columbia tax calculation"""
    income = 50000
    result = calculate_canadian_tax(income, "British Columbia")
    
    print(f"\n=== BC Test (Income: ${income:,}) ===")
    print(f"Total Tax:       ${result['total_tax']:,.2f}")
    print(f"After-Tax:       ${result['after_tax_income']:,.2f}")
    print(f"Effective Rate:  {result['effective_rate']:.2f}%")

def test_low_income():
    """Test low income with basic personal amount"""
    income = 15000
    result = calculate_canadian_tax(income, "Ontario")
    
    print(f"\n=== Low Income Test (${income:,}) ===")
    print(f"Total Tax:       ${result['total_tax']:,.2f}")
    
    # Should pay little to no tax due to basic personal amount
    assert result['total_tax'] < 500, "Low income should pay minimal tax"

if __name__ == "__main__":
    print("Running Canadian Tax Calculator Tests...\n")
    test_ontario_taxes()
    test_alberta_taxes()
    test_bc_taxes()
    test_low_income()
    print("\n✅ All tests passed!")
