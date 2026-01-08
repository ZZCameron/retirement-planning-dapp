# Test environment setup
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load test environment
test_env = Path(__file__).parent / '.env.test'
load_dotenv(test_env)

# Add backend to Python path so imports work
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path.parent))

# Mock static files for testing (prevents RuntimeError)
os.environ['TESTING'] = 'true'

import pytest
from fastapi.testclient import TestClient

# Import app only after environment is set
from backend.main import app

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)
