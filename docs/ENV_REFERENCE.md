# Environment Variable Reference

All configuration for GoTot is managed through environment variables. Copy `backend/.env.example` to `backend/.env` and fill in your values.

## Core

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | *(required)* | Secret key for JWT signing and encryption. Must be at least 32 characters. |
| `ENVIRONMENT` | `development` | `development` or `production`. Controls docs access, CSRF, HTTPS cookies. |
| `LOG_LEVEL` | `info` | Logging level: `debug`, `info`, `warning`, `error`. |

## Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://gotot:gotot_pass@localhost:5432/gotot` | Async database connection URL. Supports PostgreSQL and SQLite. |

## Redis

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection for caching, rate limiting, and pub/sub. |
| `CELERY_BROKER_URL` | `redis://localhost:6379/1` | Redis URL for Celery message broker. |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/0` | Redis URL for Celery result backend. |

## Security

| Variable | Default | Description |
|----------|---------|-------------|
| `ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated CORS origins. |
| `MAX_FILE_SIZE_MB` | `500` | Maximum file size for downloads (MB). |
| `MAX_REQUEST_SIZE_MB` | `10` | Maximum request body size (MB). |
| `RATE_LIMIT_PER_MINUTE` | `60` | Global requests per minute per IP. |
| `RATE_LIMIT_DOWNLOAD_PER_MINUTE` | `10` | Download requests per minute per IP. |

## Domain Whitelist

| Variable | Default | Description |
|----------|---------|-------------|
| `ALLOWED_DOMAINS` | `*` | Comma-separated list of allowed download domains. Use `*` for all. |

## Storage

| Variable | Default | Description |
|----------|---------|-------------|
| `DOWNLOAD_DIR` | `/tmp/downloads` | Directory for completed downloads. |
| `TEMP_DIR` | `/tmp/gotot_temp` | Temporary directory for in-progress downloads. |
| `FILE_RETENTION_HOURS` | `1` | Hours before downloaded files are eligible for cleanup. |
| `CLEANUP_INTERVAL_SECONDS` | `3600` | Seconds between automated cleanup runs. |

## Timeouts

| Variable | Default | Description |
|----------|---------|-------------|
| `DOWNLOAD_TIMEOUT` | `300` | Maximum seconds for a download operation. |
| `INFO_TIMEOUT` | `30` | Maximum seconds for video info extraction. |
| `CACHE_TTL` | `3600` | Cache time-to-live in seconds for video info. |

## JWT Authentication

| Variable | Default | Description |
|----------|---------|-------------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | JWT access token lifetime in minutes. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | JWT refresh token lifetime in days. |
| `ALGORITHM` | `HS256` | JWT signing algorithm. |

## Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `FRONTEND_URL` | `http://localhost:3000` | Public URL of the Next.js frontend. |

## Payments (Razorpay)

| Variable | Default | Description |
|----------|---------|-------------|
| `RAZORPAY_KEY_ID` | *(empty)* | Razorpay API key ID. |
| `RAZORPAY_KEY_SECRET` | *(empty)* | Razorpay API key secret. |
| `RAZORPAY_WEBHOOK_SECRET` | *(empty)* | Razorpay webhook verification secret. |
| `RAZORPAY_PRO_PLAN_ID` | *(empty)* | Razorpay plan ID for Pro tier. |
| `RAZORPAY_UNLIMITED_PLAN_ID` | *(empty)* | Razorpay plan ID for Unlimited tier. |
| `CURRENCY` | `USD` | Default currency code. |

## Email (SMTP)

| Variable | Default | Description |
|----------|---------|-------------|
| `SMTP_HOST` | *(empty)* | SMTP server hostname. |
| `SMTP_PORT` | `587` | SMTP server port. |
| `SMTP_USER` | *(empty)* | SMTP username. |
| `SMTP_PASSWORD` | *(empty)* | SMTP password. |
| `SMTP_FROM_EMAIL` | `noreply@gotot.app` | From address for system emails. |
| `ADMIN_EMAIL` | `admin@gotot.app` | Admin contact email. |
| `SUPPORT_EMAIL` | `support@gotot.app` | Support contact email. |
| `DMCA_EMAIL` | `dmca@gotot.app` | DMCA contact email. |
| `PRIVACY_EMAIL` | `privacy@gotot.app` | Privacy inquiries email. |

## Google OAuth

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_CLIENT_ID` | *(empty)* | Google OAuth client ID. |
| `GOOGLE_CLIENT_SECRET` | *(empty)* | Google OAuth client secret. |
| `GOOGLE_REDIRECT_URI` | `http://localhost:3000/auth/google/callback` | OAuth redirect URI. |

## Error Monitoring

| Variable | Default | Description |
|----------|---------|-------------|
| `SENTRY_DSN` | *(empty)* | Sentry DSN for error tracking. |

## CSRF

| Variable | Default | Description |
|----------|---------|-------------|
| `CSRF_COOKIE_NAME` | `csrf_token` | CSRF cookie name. |
| `CSRF_COOKIE_SECURE` | `true` | Set Secure flag on CSRF cookie. |
| `CSRF_COOKIE_HTTPONLY` | `true` | Set HttpOnly flag on CSRF cookie. |
| `CSRF_COOKIE_SAMESITE` | `lax` | SameSite attribute: `strict`, `lax`, or `none`. |

## Request

| Variable | Default | Description |
|----------|---------|-------------|
| `REQUEST_ID_HEADER` | `X-Request-ID` | Header name for request correlation ID. |
