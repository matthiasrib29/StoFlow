"""
Configuration centralisée de l'application Stoflow.
Charge les variables d'environnement et fournit un objet Settings.
"""
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration application via variables d'environnement."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Stoflow"
    app_env: str = Field(default="development", pattern="^(development|staging|production)$")
    debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1

    # Database
    database_url: str
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600

    # JWT
    jwt_secret_key: str
    jwt_secret_key_previous: Optional[str] = Field(
        default=None,
        description="Ancien secret JWT pour période de grâce lors de rotation"
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440
    password_hash_rounds: int = 12

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    openai_max_tokens: int = 500
    openai_temperature: float = 0.7
    ai_cache_ttl_seconds: int = 2592000
    ai_cache_enabled: bool = True

    # Vinted
    vinted_base_url: str = "https://www.vinted.fr"
    vinted_api_url: str = "https://www.vinted.fr/api/v2"
    vinted_rate_limit_max: int = 40
    vinted_rate_limit_window_hours: int = 2
    vinted_request_delay_min_seconds: int = 20
    vinted_request_delay_max_seconds: int = 50
    vinted_max_retries: int = 3
    vinted_retry_delay_seconds: int = 60

    # Logging
    log_level: str = "DEBUG"
    log_format: str = "detailed"
    log_file_enabled: bool = True
    log_file_path: str = "logs/stoflow.log"
    log_file_max_bytes: int = 10485760
    log_file_backup_count: int = 5

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8080"
    cors_allow_credentials: bool = True

    # User schema isolation
    user_schema_prefix: str = "user_"
    user_max_schemas: int = 1000

    # Monitoring
    sentry_dsn: Optional[str] = None
    sentry_environment: str = "development"
    sentry_traces_sample_rate: float = 0.1

    def get_cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Using lru_cache ensures settings are loaded only once.
    """
    return Settings()


# Instance globale pour import facile
settings = get_settings()
