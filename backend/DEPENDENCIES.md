# Dependency Management

## Installation

### Production Environment
```bash
pip install -r requirements.txt

"""
File Structure
requirements.txt - Production dependencies only (what's deployed)
requirements-dev.txt - Development dependencies (includes production via -r requirements.txt)
"""

# Updating Dependencies
## Add Production Dependency
pip install new-package==1.0.0
# Manually add to requirements.txt
echo "new-package==1.0.0" >> requirements.txt

## Add Development Dependency
pip install new-dev-tool==2.0.0

## Manually add to requirements-dev.txt
echo "new-dev-tool==2.0.0" >> requirements-dev.txt

## Check for Outdated Packages
pip list --outdated

"""
Why Separate?
    Smaller production deployments - Don't deploy pytest to production
    Security - Fewer packages = smaller attack surface
    Build speed - Production Docker images build faster
    Clarity - Clear distinction between runtime and development needs
Current Production Dependencies
    FastAPI, Uvicorn - Web framework
    Pydantic - Data validation
    NumPy, Pandas, SciPy - Financial calculations
    Python-JOSE, Passlib, Bcrypt - Authentication
    HTTPx - HTTP client
    Python-dotenv - Configuration
Current Development Dependencies
    pytest 8.3.3, pytest-cov - Testing
    black, isort - Code formatting
    flake8, pylint - Linting
    mypy - Type checking
    bandit - Security scanning
    pre-commit - Git hooks
    ipython, ipdb - Development REPL
"""