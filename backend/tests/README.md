# Test Suite

## Overview

Comprehensive test suite for the Canadian Retirement Planning DApp backend.

## Running Tests

### Run all tests
```bash
cd ~/retirement-planning-dapp
source backend/venv/bin/activate
pytest backend/tests/ -v

## Run specific test file
pytest backend/tests/unit/test_tax_calculator.py -v

## Run with detailed output
pytest backend/tests/unit/test_tax_calculator.py -v -s

## Run with coverage report
pytest backend/tests/ --cov=backend --cov-report=html --cov-report=term
# Open htmlcov/index.html in browser to see detailed coverage

## Run as Python module (alternative)
python3 -m backend.tests.unit.test_tax_calculator

"""
Test Structure
backend/tests/
├── __init__.py
├── README.md                    # This file
├── unit/                        # Unit tests (isolated components)
│   ├── __init__.py
│   └── test_tax_calculator.py   # Tax calculation tests
└── integration/                 # Integration tests (API endpoints)
    └── __init__.py
Current Test Coverage
Tax Calculator Tests (test_tax_calculator.py)
Tests for Canadian federal and provincial tax calculations using 2024 tax rates.

Test Cases:

test_ontario_taxes() - Ontario tax at $100k income with graduated rates
test_alberta_taxes() - Alberta flat 10% rate comparison
test_bc_taxes() - British Columbia tax calculation
test_low_income() - Low income with basic personal amount
Key Validations:

Federal tax calculations with 2024 brackets
Provincial tax for all Canadian provinces
Basic personal amount (BPA) tax credits
Effective and marginal tax rates
After-tax income calculations
Ontario vs Alberta comparison at $100k (Alberta pays ~$1,765 more)
"""

# Adding New Tests
## Unit Tests
## Create new test files in backend/tests/unit/:
"""
Test module description
"""
from backend.models.your_module import YourClass

def test_your_feature():
    """Test description"""
    # Arrange
    input_data = ...
    
    # Act
    result = YourClass.method(input_data)
    
    # Assert
    assert result == expected_value

# Integration Tests
Create new test files in backend/tests/integration/ for API endpoint testing.

"""
Test Standards
Naming: Test files start with test_, test functions start with test_
Docstrings: All test functions have descriptive docstrings
Assertions: Clear assertion messages for failures
Isolation: Unit tests don't depend on external services
Coverage: Aim for >80% code coverage for production code
"""

# Troubleshooting
## Module Import Errors
If you see ModuleNotFoundError: No module named 'backend':
# Run from project root as a module
cd ~/retirement-planning-dapp
python3 -m backend.tests.unit.test_tax_calculator

# pytest Configuration Errors
## If pytest complains about missing coverage plugin:
pip install pytest-cov

## Or run without coverage:
pytest --no-cov

"""
Future Test Additions
 Retirement calculator logic tests
 RRIF withdrawal calculation tests
 CPP/OAS calculation tests
 Pension income integration tests
 API endpoint integration tests
 Allocation strategy tests
 """
