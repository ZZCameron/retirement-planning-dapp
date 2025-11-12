"""
Setup configuration for retirement planning backend.
"""

from setuptools import setup, find_packages

setup(
    name="retirement-planning-backend",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.12",
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "pydantic>=2.6.0",
        "pydantic-settings>=2.1.0",
        "numpy>=1.26.0",
        "pandas>=2.2.0",
        "scipy>=1.12.0",
    ],
)
