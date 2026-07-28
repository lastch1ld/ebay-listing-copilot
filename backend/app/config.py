from enum import StrEnum

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ebay_environment: Environment = Environment.SANDBOX
    ebay_client_id: str = ""
    ebay_client_secret: SecretStr = Field(default=SecretStr(""))
    ebay_redirect_uri: str = "http://127.0.0.1:8000/api/auth/ebay/callback"
    openai_api_key: SecretStr = Field(default=SecretStr(""))
    openai_model: str = ""
    tracking_provider_base_url: str = ""
    database_url: str = "sqlite:///./data/app.db"


def load_settings() -> Settings:
    return Settings()
