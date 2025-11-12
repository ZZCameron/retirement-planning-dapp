"""
Setup configuration for retirement planning backend.
"""

from setuptools import setup, find_packages

setup(
    name="retirement-planning-backend",
    version="0.1.0",
    packages=find_packages(include=["backend", "backend.*"]),
    python_requires=">=3.12",
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "pydantic>=2.6.0",
        "pydantic-settings>=2.1.0",
        "numpy>=1.26.0",
        "pandas>=2.2.0",
        "scipy>=1.12.0",
        "numpy-financial>=1.0.0",
        "python-multipart>=0.0.7",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "python-dotenv>=1.0.1",
        "httpx>=0.26.0",
    ],
)
