#!/usr/bin/env python3
"""
Verify development environment setup.
Run this to ensure everything is configured correctly.
"""

import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Verify Python version is 3.12+"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 12:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python version {version.major}.{version.minor} - Need 3.12+")
        return False


def check_virtual_env():
    """Verify running in virtual environment"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment active")
        return True
    else:
        print("❌ Not in virtual environment - run: source venv/bin/activate")
        return False


def check_dependencies():
    """Check if key dependencies are installed"""
    try:
        import fastapi
        import pydantic
        import numpy
        import pandas
        print("✅ Core dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False


def check_project_structure():
    """Verify project structure exists"""
    required_dirs = [
        "backend/src/api/v1",
        "backend/src/models",
        "backend/src/services",
        "backend/tests/unit",
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path}")
        else:
            print(f"❌ Missing: {dir_path}")
            all_exist = False
    
    return all_exist


def check_env_file():
    """Verify .env file exists"""
    if Path(".env").exists():
        print("✅ .env file exists")
        return True
    else:
        print("❌ .env file missing - copy from .env.example")
        return False


def main():
    print("=" * 60)
    print("Retirement Planning DApp - Setup Verification")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_env),
        ("Dependencies", check_dependencies),
        ("Project Structure", check_project_structure),
        ("Environment File", check_env_file),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\nChecking {name}:")
        results.append(check_func())
    
    print("\n" + "=" * 60)
    if all(results):
        print("🎉 All checks passed! You're ready to start developing.")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
