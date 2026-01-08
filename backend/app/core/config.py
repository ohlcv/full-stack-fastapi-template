import secrets
import warnings
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    HttpUrl,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    FRONTEND_HOST: str = "http://localhost:5173"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    PROJECT_NAME: str
    SENTRY_DSN: HttpUrl | None = None
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: str | None = None

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    EMAIL_TEST_USER: EmailStr = "test@example.com"
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    # Redis configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def REDIS_URL(self) -> str:
        """Get Redis connection URL."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Cache configuration
    CACHE_EXPIRE_SECONDS: int = 300  # 5 minutes default
    CACHE_KEY_PREFIX: str = "app:cache:"

    # ARQ configuration
    ARQ_REDIS_URL: str | None = None  # If None, uses REDIS_URL

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ARQ_REDIS_CONNECTION(self) -> str:
        """Get ARQ Redis connection URL."""
        return self.ARQ_REDIS_URL or self.REDIS_URL

    # Rate limiting configuration
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_STORAGE_URI: str | None = None  # If None, uses REDIS_URL

    @computed_field  # type: ignore[prop-decorator]
    @property
    def RATE_LIMIT_STORAGE(self) -> str:
        """Get rate limiting storage URL."""
        return self.RATE_LIMIT_STORAGE_URI or self.REDIS_URL

    # Default rate limits (requests per time period)
    RATE_LIMIT_DEFAULT: str = "100/minute"  # Default: 100 requests per minute
    RATE_LIMIT_LOGIN: str = "5/minute"  # Login: 5 requests per minute
    RATE_LIMIT_REGISTER: str = "3/minute"  # Register: 3 requests per minute
    RATE_LIMIT_PASSWORD_RESET: str = "3/hour"  # Password reset: 3 requests per hour

    # Internationalization (i18n) configuration
    I18N_ENABLED: bool = True
    I18N_DEFAULT_LOCALE: str = "zh_CN"  # Default locale: Chinese (Simplified)
    I18N_SUPPORTED_LOCALES: list[str] = ["zh_CN", "en_US"]  # Supported locales
    I18N_LOCALE_DIR: str = "app/locales"  # Translation files directory

    # File upload configuration
    UPLOAD_DIR: str = "uploads"  # Base directory for file uploads
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB default
    ALLOWED_EXTENSIONS: list[str] = [
        ".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx", ".txt"
    ]  # Allowed file extensions
    ALLOWED_MIME_TYPES: list[str] = [
        "image/jpeg", "image/png", "image/gif",
        "application/pdf", "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
    ]  # Allowed MIME types

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )

        return self


settings = Settings()  # type: ignore
