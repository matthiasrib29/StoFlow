"""
Configuration centralisée de l'application Stoflow.
Charge les variables d'environnement et fournit un objet Settings.
"""
import os
from functools import lru_cache
from pathlib import Path
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
    app_env: str = Field(
        default="development",
        pattern="^(development|test|staging|production)$",
        description="Environment: development, test, staging, or production (Security 2026-01-12)"
    )
    debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1

    # Database
    database_url: str
    db_pool_size: int = 10  # Increased from 5 for better concurrency
    db_max_overflow: int = 20  # Increased from 10 for peak load
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600

    # JWT
    jwt_secret_key: str
    jwt_secret_key_previous: Optional[str] = Field(
        default=None,
        description="Ancien secret JWT pour période de grâce lors de rotation"
    )
    jwt_algorithm: str = "RS256"  # Migré de HS256 vers RS256 asymétrique
    jwt_private_key_path: str = Field(default="keys/private_key.pem")
    jwt_public_key_path: str = Field(default="keys/public_key.pem")
    jwt_private_key_pem: Optional[str] = Field(
        default=None,
        description="Clé privée RSA (chargée depuis fichier ou env)"
    )
    jwt_public_key_pem: Optional[str] = Field(
        default=None,
        description="Clé publique RSA (chargée depuis fichier ou env)"
    )
    jwt_access_token_expire_minutes: int = 15  # Changé de 1440 (24h) à 15 min
    jwt_refresh_token_expire_days: int = 7
    password_hash_rounds: int = 12

    # Encryption (for sensitive data at rest)
    encryption_key: Optional[str] = Field(
        default=None,
        description="Fernet key for encrypting OAuth tokens. Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
    )
    encryption_key_previous: Optional[str] = Field(
        default=None,
        description="Previous encryption key for rotation support"
    )

    # AI Services
    ai_cache_ttl_seconds: int = 2592000
    ai_cache_enabled: bool = True

    # Google Gemini Vision
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3-flash-preview"
    gemini_max_images: int = 10
    gemini_timeout_seconds: float = 30.0      # Timeout per API call
    gemini_max_retries: int = 1               # Max retry attempts
    gemini_retry_backoff_factor: float = 2.0  # Exponential backoff multiplier

    # HTTP Client (Centralized timeouts)
    http_timeout_connect: float = 10.0  # Connection timeout in seconds
    http_timeout_read: float = 30.0  # Read timeout in seconds
    http_timeout_write: float = 30.0  # Write timeout in seconds
    http_timeout_pool: float = 10.0  # Pool timeout in seconds
    http_max_retries: int = 3  # Max retries for failed requests
    http_retry_backoff_factor: float = 1.0  # Backoff factor (1s, 2s, 4s)

    # Vinted
    vinted_base_url: str = "https://www.vinted.fr"
    vinted_api_url: str = "https://www.vinted.fr/api/v2"
    vinted_rate_limit_max: int = 40
    vinted_rate_limit_window_hours: int = 2
    vinted_request_delay_min_seconds: int = 20
    vinted_request_delay_max_seconds: int = 50
    vinted_max_retries: int = 3
    vinted_retry_delay_seconds: int = 60

    # Plugin WebSocket Timeouts (Vinted operations via browser extension)
    plugin_timeout_default: int = 60   # Default timeout
    plugin_timeout_publish: int = 60   # Publish/update operations
    plugin_timeout_delete: int = 30    # Delete operations
    plugin_timeout_upload: int = 30    # Image upload
    plugin_timeout_sync: int = 60      # Sync operations
    plugin_timeout_order: int = 60     # Order sync operations

    # Logging
    log_level: str = "DEBUG"
    log_format: str = "detailed"
    log_file_enabled: bool = True
    log_file_path: str = "logs/stoflow.log"
    log_file_max_bytes: int = 10485760
    log_file_backup_count: int = 5

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:8080"
    cors_allow_credentials: bool = True

    # User schema isolation
    user_schema_prefix: str = "user_"
    user_max_schemas: int = 1000

    # Monitoring
    sentry_dsn: Optional[str] = None
    sentry_environment: str = "development"
    sentry_traces_sample_rate: float = 0.1

    # Brevo (Email Service)
    brevo_api_key: Optional[str] = None
    brevo_sender_email: str = "noreply@stoflow.io"
    brevo_sender_name: str = "StoFlow"
    frontend_url: str = "http://localhost:3000"

    @property
    def brevo_enabled(self) -> bool:
        """Check if Brevo email service is configured."""
        return bool(self.brevo_api_key)

    # Cloudflare R2 Storage
    r2_account_id: Optional[str] = None
    r2_access_key_id: Optional[str] = None
    r2_secret_access_key: Optional[str] = None
    r2_bucket_name: str = "stoflow-images"
    r2_endpoint: Optional[str] = None  # https://<account_id>.r2.cloudflarestorage.com
    r2_public_url: Optional[str] = None  # https://cdn.stoflow.io or R2 public URL

    @property
    def r2_enabled(self) -> bool:
        """Check if R2 storage is configured."""
        return bool(
            self.r2_access_key_id
            and self.r2_secret_access_key
            and self.r2_endpoint
        )

    @property
    def storage_base_url(self) -> str:
        """Get the base URL for serving images."""
        if self.r2_public_url:
            return self.r2_public_url.rstrip("/")
        # Fallback to local uploads
        return ""

    def model_post_init(self, __context) -> None:
        """Charger les clés RSA après initialisation (Pydantic v2)."""
        # Charger les clés depuis les fichiers PEM si pas déjà définies
        if not self.jwt_private_key_pem:
            private_key_file = Path(self.jwt_private_key_path)
            if private_key_file.exists():
                self.jwt_private_key_pem = private_key_file.read_text()

        if not self.jwt_public_key_pem:
            public_key_file = Path(self.jwt_public_key_path)
            if public_key_file.exists():
                self.jwt_public_key_pem = public_key_file.read_text()

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
