"""
Integration tests for API endpoints.
"""

import pytest
from fastapi import status


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns health info."""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "online"
        assert "version" in data
    
    def test_health_endpoint(self, client):
        """Test /health endpoint."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"


class TestRetirementAPI:
    """Test retirement planning API endpoints."""
    
    def test_calculate_endpoint_valid_input(self, client, sample_plan_input):
        """Test calculation with valid input."""
        response = client.post(
            "/api/v1/retirement/calculate",
            json=sample_plan_input.model_dump()
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "projections" in data
        assert "final_balance" in data
        assert "success" in data
        assert "recommendations" in data
        assert len(data["projections"]) > 0
    
    def test_calculate_endpoint_invalid_age(self, client, sample_plan_input):
        """Test calculation with invalid retirement age."""
        invalid_input = sample_plan_input.model_copy()
        invalid_input.retirement_age = 30
        
        response = client.post(
            "/api/v1/retirement/calculate",
            json=invalid_input.model_dump()
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_rules_endpoint(self, client):
        """Test getting retirement rules."""
        response = client.get("/api/v1/retirement/rules")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "rrsp_contribution_limit" in data
        assert "cpp_max_monthly_at_65" in data
        assert "oas_max_monthly_65_74" in data


class TestRetirementAPIErrorHandling:
    """Test error handling in retirement API."""
    
    def test_calculate_negative_age(self, client):
        """Test API rejects negative age (ValueError path)."""
        invalid_data = {
            "current_age": -5,  # Invalid!
            "retirement_age": 65,
            "life_expectancy": 90,
            "province": "Ontario",
            "rrsp_balance": 50000,
            "tfsa_balance": 20000,
            "non_registered": 0,
            "monthly_contribution": 1000,
            "expected_return": 0.07,
            "expected_inflation": 0.025,
            "cpp_monthly": 1200,
            "cpp_start_age": 65,
            "oas_start_age": 65,
            "desired_annual_spending": 50000,
            "has_spouse": false
        }
        
        response = client.post(
            "/api/v1/retirement/calculate",
            json=invalid_data
        )
        
        # Should return 422 Unprocessable Entity
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        # This tests lines 56-60!
    
    def test_calculate_retirement_before_current_age(self, client, sample_plan_input):
        """Test API rejects retirement age before current age."""
        invalid_input = sample_plan_input.model_copy()
        invalid_input.retirement_age = 30  # Before current_age of 35
        
        response = client.post(
            "/api/v1/retirement/calculate",
            json=invalid_input.model_dump()
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        # Also tests lines 56-60
    
    def test_calculate_invalid_return_rate(self, client, sample_plan_input):
        """Test API rejects invalid return rate."""
        invalid_input = sample_plan_input.model_copy()
        invalid_input.expected_return = 1.5  # 150% return - unrealistic!
        
        response = client.post(
            "/api/v1/retirement/calculate",
            json=invalid_input.model_dump()
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        # Tests validation error handling
