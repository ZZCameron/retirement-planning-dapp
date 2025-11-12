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
        
        # Check response structure
        assert "projections" in data
        assert "final_balance" in data
        assert "success" in data
        assert "recommendations" in data
        
        # Check projections
        assert len(data["projections"]) > 0
    
    def test_calculate_endpoint_invalid_age(self, client, sample_plan_input):
        """Test calculation with invalid retirement age."""
        invalid_input = sample_plan_input.model_copy()
        invalid_input.retirement_age = 30  # Before current age
        
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
        
        # Check key fields exist
        assert "rrsp_contribution_limit" in data
        assert "cpp_max_monthly_at_65" in data
        assert "oas_max_monthly_65_74" in data
