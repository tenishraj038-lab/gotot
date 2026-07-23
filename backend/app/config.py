from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    secret_key: str
    database_url: str = "postgresql+asyncpg://gotot:gotot_pass@localhost:5432/gotot"
    redis_url: str = "redis://localhost:6379/0"
    environment: str = "development"
    log_level: str = "info"
    sentry_dsn: str = ""
    allowed_origins: str = "http://localhost:3000"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/0"
    max_file_size_mb: int = 500
    max_request_size_mb: int = 10
    rate_limit_per_minute: int = 60
    rate_limit_download_per_minute: int = 10
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    algorithm: str = "HS256"
    frontend_url: str = "http://localhost:3000"
    download_dir: str = "/tmp/downloads"
    temp_dir: str = "/tmp/gotot_temp"
    download_timeout: int = 300
    info_timeout: int = 30
    cache_ttl: int = 3600
    file_retention_hours: int = 1
    cleanup_interval_seconds: int = 3600
    allowed_domains: str = "*"
    download_retries: int = 3
    download_retry_backoff: float = 2.0
    merge_timeout: int = 180
    ffprobe_timeout: int = 15
    cookies_dir: str = "/tmp/gotot_cookies"

    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""
    razorpay_pro_plan_id: str = ""
    razorpay_unlimited_plan_id: str = ""
    currency: str = "USD"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@gotot.app"
    admin_email: str = "admin@gotot.app"
    support_email: str = "support@gotot.app"
    dmca_email: str = "dmca@gotot.app"
    privacy_email: str = "privacy@gotot.app"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:3000/auth/google/callback"

    request_id_header: str = "X-Request-ID"
    csrf_cookie_name: str = "csrf_token"
    csrf_cookie_secure: bool = True
    csrf_cookie_httponly: bool = True
    csrf_cookie_samesite: str = "lax"

    model_config = {"env_file": ".env", "case_sensitive": False}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
