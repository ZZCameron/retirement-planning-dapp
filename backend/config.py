"""
Configuration management using Pydantic Settings.
This ensures type safety and validation of environment variables.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Never hardcode sensitive values!
    """

    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = Field(default="Retirement Planning DApp")
    app_version: str = Field(default="0.1.0")
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = Field(default=False)

    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, ge=1024, le=65535)
    api_reload: bool = Field(default=True)

    # Security
    secret_key: str = Field(min_length=32)
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, ge=5, le=1440)

    # CORS
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:8000,https://www.web3-retirement-plan.com,https://web3-retirement-plan.com,https://retirement-planning-dapp-git-develop-robert-camerons-projects.vercel.app")

    # Payment Configuration (ADD HERE - same indentation as cors_origins)
    treasury_wallet: str = Field(
        default="4m5yJZMSYK2N6htdkwQ8t4dsmuRSxuZ2rDba51cFc25m",  # Staging default
        env="TREASURY_WALLET",  # Reads from Railway environment variable
        description="Treasury wallet for receiving payments"
    )
    payment_amount_sol: float = Field(
        default=0.001,
        ge=0.0001,
        le=1.0,
        description="Required payment amount in SOL"
    )

    # Solana
    solana_network: Literal["devnet", "testnet", "mainnet-beta"] = "devnet"
    solana_rpc_url: str = Field(default="https://api.devnet.solana.com")

    # Database
    database_url: str = Field(default="sqlite:///./retirement_planning.db")

    # Rate Limiting
    rate_limit_requests: int = Field(default=100, ge=1)
    rate_limit_period: int = Field(default=60, ge=1)

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Ensure secret key is strong in production."""
        # Access other field values through info.data
        environment = info.data.get("environment")
        if environment == "production" and "change-this" in v.lower():
            raise ValueError("Must set a strong SECRET_KEY in production!")
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        """Convert CORS origins string to list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance.
    This ensures we only load environment variables once.
    """
    return Settings()

# For convenience
settings = get_settings()
