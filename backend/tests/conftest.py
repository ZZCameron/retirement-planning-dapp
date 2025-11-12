"""
Pytest configuration and fixtures.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.retirement_plan import RetirementPlanInput
from backend.models.canadian_rules import Province


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_plan_input():
    """Sample valid retirement plan input."""
    return RetirementPlanInput(
        current_age=35,
        retirement_age=65,
        life_expectancy=90,
        province=Province.ON,
        rrsp_balance=50000,
        tfsa_balance=20000,
        non_registered=10000,
        monthly_contribution=1000,
        expected_return=0.07,
        expected_inflation=0.025,
        cpp_monthly=1200,
        cpp_start_age=65,
        oas_start_age=65,
        desired_annual_spending=50000,
        has_spouse=False,
    )
