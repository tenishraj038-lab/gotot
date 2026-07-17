# GoTot Security Documentation

Comprehensive overview of security measures implemented across the GoTot platform.

---

## Table of Contents

- [Authentication](#authentication)
- [Authorization](#authorization)
- [CSRF Protection](#csrf-protection)
- [Rate Limiting](#rate-limiting)
- [Input Validation](#input-validation)
- [SQL Injection Prevention](#sql-injection-prevention)
- [XSS Prevention](#xss-prevention)
- [Path Traversal Protection](#path-traversal-protection)
- [Security Headers](#security-headers)
- [CORS Configuration](#cors-configuration)
- [Dependency Security](#dependency-security)
- [Secret Management](#secret-management)
- [Logging and Audit Trail](#logging-and-audit-trail)

---

## Authentication

### JWT (JSON Web Tokens)

GoTot uses **python-jose** with HS256 (HMAC with SHA-256) for JWT signing.

| Setting | Value |
|---------|-------|
| Algorithm | HS256 |
| Access token expiry | 60 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`) |
| Refresh token expiry | 30 days (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`) |

Access token payload:
```json
{
  "sub": "user-uuid",
  "role": "free",
  "type": "access",
  "exp": 1710512345
}
```

Refresh token payload:
```json
{
  "sub": "user-uuid",
  "type": "refresh",
  "ver": 3,
  "exp": 1713104345
}
```

### Refresh Token Rotation

Each time a refresh token is used:
1. The current `refresh_token_version` is checked against the token's `ver` claim.
2. If they don't match, the token is considered revoked and the user must log in again.
3. If they match, `refresh_token_version` is **incremented** in the database.
4. A new token pair is issued with the new version.

This ensures that if a refresh token is stolen, the legitimate user's next refresh will fail (the version was already incremented by the attacker), and the user will know their session was compromised.

### Password Hashing

Passwords are hashed using **bcrypt** via `passlib`:

```python
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
```

- Salt: Auto-generated (12 rounds)
- Comparison: Constant-time `checkpw` to prevent timing attacks

### Password Requirements

- Minimum 8 characters
- At least one uppercase letter
- At least one digit

### Google OAuth

Google ID tokens are verified against Google's token info endpoint:
```python
resp = await client.get(
    "https://oauth2.googleapis.com/tokeninfo",
    params={"id_token": data.id_token},
)
```

Additional checks:
- `aud` (audience) must match the configured `GOOGLE_CLIENT_ID`
- `email` must be present
- Token is verified via HTTPS to Google's API (not decoded locally)

### API Key Authentication

API keys use a **SHA-256 hash** stored in the database:

```python
raw_key = "gt_" + secrets.token_hex(32)
hashed = hashlib.sha256(key.encode()).hexdigest()
```

- Keys are 66 characters long (prefix + 64 hex chars)
- Only the **hash** is stored — if the database is compromised, keys cannot be recovered
- The raw key is shown **only once** at creation time
- Rate-limited per key per day
- Keys can be revoked (soft delete via `is_active = false`)

---

## Authorization

### Role-Based Access

| Role | Access |
|------|--------|
| `admin` | All admin endpoints (`/admin/*`) |
| `pro` / `unlimited` | Premium features (concurrent downloads, API access) |
| `free` | Basic features with rate limits |

### Admin Authorization

All admin routes require a middleware check:

```python
async def require_admin(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
```

### Admin-Specific Protections

- **Delete user**: Cannot delete admin users
  ```python
  if user.is_admin:
      raise HTTPException(status_code=403, detail="Cannot delete admin users")
  ```
- All admin actions are logged to the audit trail

### Anonymous User Limits

- Anonymous users can download videos without authentication
- Download history for anonymous users returns an empty list (privacy)
- Anonymous users cannot access subscription features, API keys, or referrals

---

## CSRF Protection

### Implementation

CSRF protection is implemented via a **double-submit cookie pattern** in production only.

**Middleware** (`backend/app/middleware/csrf.py`):
- On every GET/HEAD/OPTIONS request: sets a `csrf_token` cookie (32-byte hex, httponly, samesite=lax)
- On every mutating request: validates that `X-CSRF-Token` header matches the cookie

### Exempt Paths

```python
CSRF_EXEMPT_PATHS = {
    "/health",
    "/contact",
    "/auth/register",
    "/auth/login",
    "/auth/refresh",
}
```

### Skip Conditions

CSRF is skipped if the request already has:
- A valid `Authorization: Bearer <token>` header (authenticated API calls)
- A valid `X-API-Key: gt_...` header (programmatic access)

### Cookie Settings

| Attribute | Development | Production |
|-----------|-------------|-----------|
| `httponly` | true | true |
| `samesite` | lax | lax |
| `secure` | false | true |
| `max_age` | 3600s | 3600s |

---

## Rate Limiting

### Implementation

Rate limiting uses **SlowAPI** with a Redis storage backend:

```python
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
    storage_uri=settings.redis_url,
)
```

### Limits by Auth Method

| Auth Type | Rate Limit |
|-----------|-----------|
| Anonymous IP | 60 req/min |
| Authenticated (Bearer token) | 60 req/min (free), 120 (pro), 300 (unlimited) |
| API key | Per-key daily limit (50/1K/10K) |

### Response

When rate limited, the API returns:
```
HTTP 429 Too Many Requests
Retry-After: 60
```

```json
{
  "detail": "Rate limit exceeded: 60 per 1 minute"
}
```

---

## Input Validation

### Pydantic Models

All request bodies are validated using Pydantic v2 models:

```python
class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address")
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain an uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain a digit")
        return v
```

### URL Validation

```python
def is_valid_url(url: str) -> bool:
    regex = re.compile(
        r"^https?://"
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
        r"localhost|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        r"(?::\d+)?"
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return bool(regex.match(url))
```

### Input Sanitization

- **Username**: Alphanumeric only, 3+ characters
- **Name** (contact form): 2-100 characters, stripped whitespace
- **Message** (contact form): 10-2000 characters, stripped whitespace
- **Email**: Lowercased and stripped
- **Search query**: Stripped of SQL wildcard characters (`\`, `%`, `_`) using `re.sub`

---

## SQL Injection Prevention

GoTot uses **SQLAlchemy 2.0** with **parameterized queries** exclusively. Raw SQL is never concatenated with user input.

### Safe (parameterized)

```python
result = await db.execute(
    select(User).where(User.email == data.email)
)
```

```python
result = await db.execute(
    select(User).where(
        (User.email.ilike(search_filter)) |
        (User.username.ilike(search_filter))
    )
)
```

### Unsafe (never used)

```python
# NEVER concatenate user input into SQL
await db.execute(f"SELECT * FROM users WHERE email = '{data.email}'")
```

### Search Queries

The one case using `text()` is a safe aggregate:

```python
.group_by(text("day"))
```

User search input is sanitized before `ilike`:
```python
safe_q = re.sub(r'[\\%_]', '', q)
result = await db.execute(
    select(DownloadHistory)
    .where(DownloadHistory.url.ilike(f"%{safe_q}%"))
)
```

---

## XSS Prevention

### Backend

- All user-provided text is stored as-is (no HTML rendering expected)
- Error messages use Pydantic validation, not raw user input
- Content-Type headers are explicit for file downloads

### Frontend (Next.js)

React/Next.js escapes all rendered content by default using JSX:

```tsx
{/* Safe - React escapes userInput */}
<div>{userInput}</div>

{/* Only use dangerouslySetInnerHTML if absolutely necessary */}
<div dangerouslySetInnerHTML={{ __html: sanitizedHtml }} />
```

The frontend does not use `dangerouslySetInnerHTML` anywhere in the codebase.

### Content Security Policy

In production, the backend sets a strict CSP:

```
default-src 'self'
script-src 'self' 'unsafe-inline' 'unsafe-eval' https://checkout.razorpay.com https://www.googletagmanager.com
style-src 'self' 'unsafe-inline' https://fonts.googleapis.com
img-src 'self' data: https: blob:
font-src 'self' https://fonts.gstatic.com
connect-src 'self' https://api.razorpay.com https://sentry.io
frame-src 'self' https://checkout.razorpay.com
media-src 'self'
object-src 'none'
```

---

## Path Traversal Protection

File serving is protected against path traversal attacks:

```python
@router.get("/file/{filename}")
async def serve_file(filename: str, ...):
    safe_name = os.path.basename(filename)  # Strip directory components
    resolved_path = os.path.realpath(os.path.join(settings.download_dir, safe_name))

    # Ensure resolved path is within the download directory
    if not resolved_path.startswith(os.path.realpath(settings.download_dir)):
        raise HTTPException(status_code=403, detail="Invalid file path")

    if not os.path.exists(resolved_path):
        raise HTTPException(status_code=404, detail="File not found or expired")
```

Checks performed:
1. `os.path.basename()` — removes any directory traversal (`../../etc/passwd` → `passwd`)
2. `os.path.realpath()` — resolves symlinks and relative paths to absolute
3. `startswith()` — ensures the resolved path is within the allowed download directory

---

## Security Headers

Set by `SecurityHeadersMiddleware` in `backend/app/middleware/security.py`:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevents MIME type sniffing |
| `X-Frame-Options` | `DENY` | Prevents clickjacking |
| `X-XSS-Protection` | `1; mode=block` | Enables browser XSS filter |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` | Enforces HTTPS |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Controls referrer header |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | Restricts API access |
| `X-Request-ID` | `<uuid>` | Request tracing |
| `X-DNS-Prefetch-Control` | `off` | Disables DNS prefetching |
| `X-Download-Options` | `noopen` | Prevents automatic file opening |
| `Cross-Origin-Resource-Policy` | `same-origin` | Restricts resource loading |
| `Cross-Origin-Opener-Policy` | `same-origin` | Isolates browsing context |

Nginx also sets HSTS with a longer max-age:
```
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
```

---

## CORS Configuration

```python
origins = [o.strip() for o in settings.allowed_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization", "Content-Type", "X-Request-ID",
        "X-Razorpay-Signature", "X-Ad-Completed", "X-API-Key",
        "X-CSRF-Token", "X-Google-Token",
    ],
    expose_headers=["X-Request-ID"],
    max_age=600,
)
```

**Production setting:**
```
ALLOWED_ORIGINS=https://gotot.app,https://www.gotot.app
```

**Development setting:**
```
ALLOWED_ORIGINS=http://localhost:3000
```

---

## Dependency Security

### Dependency Scanning

- All dependencies are pinned with exact versions in `requirements.txt` and `package.json`
- Regular `npm audit` and `pip audit` scanning recommended
- Dependencies are cached in CI with hash-locked lockfiles (`package-lock.json`)

### Key Libraries and Their Security Properties

| Library | Version | Security Notes |
|---------|---------|----------------|
| `python-jose` | 3.3.0 | JWT with HS256 |
| `passlib[bcrypt]` | 1.7.4 | Bcrypt hashing (12 rounds) |
| `slowapi` | 0.1.9 | Redis-backed rate limiting |
| `sentry-sdk` | 2.6.0 | Error tracking, no PII sent |
| `yt-dlp` | latest | External download tool, runs in isolated process |
| `bcrypt` | (via passlib) | Constant-time comparison |
| `cryptography` | (via python-jose) | Cryptographic operations |

### Container Security

- Python 3.12-slim base image (minimal attack surface)
- Non-root user (`gotot`, UID 1000) in backend container
- Non-root user (`nextjs`, UID 1001) in frontend container
- Alpine-based nginx and redis images

---

## Secret Management

### Environment Variables

All secrets are managed through environment variables, never hardcoded:

```
SECRET_KEY=                       # JWT signing key (64-byte hex)
RAZORPAY_KEY_ID=                  # Razorpay API key
RAZORPAY_KEY_SECRET=              # Razorpay API secret
RAZORPAY_WEBHOOK_SECRET=          # Razorpay webhook signing secret
SMTP_PASSWORD=                    # SMTP/email service password
GOOGLE_CLIENT_SECRET=             # Google OAuth secret
SENTRY_DSN=                       # Sentry error tracking DSN
POSTGRES_PASSWORD=                # Database password
REDIS_REQUIREPASS=                # Redis password
```

### Environment Files

- `backend/.env` — Backend secrets (never committed to Git)
- `frontend/.env.local` — Frontend variables (NEXT_PUBLIC_* only)
- `.env` — Docker Compose variables (database/redis passwords)

### .gitignore

`.env` files are excluded from version control via `.gitignore`.

### Nginx Protection

Nginx blocks access to sensitive paths:
```nginx
location ~ /\.git { deny all; }
location ~ /\.env { deny all; }
```

---

## Logging and Audit Trail

### HTTP Request Logging

Every request is logged in structured JSON format:

```json
{
  "timestamp": "2026-03-15T10:30:00.123Z",
  "request_id": "a1b2c3d4",
  "method": "POST",
  "path": "/auth/login",
  "query": "",
  "status": 200,
  "elapsed_ms": 45,
  "ip": "203.0.113.42",
  "user_agent": "Mozilla/5.0...",
  "content_length": 256
}
```

Log levels:
- `< 400` → INFO
- `400-499` → WARNING
- `>= 500` → ERROR

### Audit Log Database

All security-relevant actions are stored in the `audit_logs` table:

| Action | Description |
|--------|-------------|
| `LOGIN_SUCCESS` | Successful authentication |
| `LOGIN_FAILED` | Failed authentication attempt |
| `REGISTER` | New user registration |
| `DOWNLOAD` | Video download completed |
| `PAYMENT` | Payment transaction |
| `ADMIN_TOGGLE_BAN` | User banned/unbanned |
| `ADMIN_CANCEL_SUBSCRIPTION` | Subscription canceled by admin |
| `ADMIN_DELETE_USER` | User account deleted |
| `ADMIN_CREATE_FEATURE_FLAG` | Feature flag created |
| `ADMIN_TOGGLE_FEATURE_FLAG` | Feature flag toggled |
| `ADMIN_CREATE_AFFILIATE` | Affiliate link created |
| `ADMIN_UPDATE_AFFILIATE` | Affiliate link updated |
| `ADMIN_DELETE_AFFILIATE` | Affiliate link deleted |

### Audit Log Format

```json
{
  "id": "uuid",
  "action": "LOGIN_SUCCESS",
  "user_id": "uuid",
  "email": "user@example.com",
  "ip_address": "203.0.113.42",
  "resource": null,
  "details": {},
  "status": "success",
  "created_at": "2026-03-15T10:30:00"
}
```

### Sentry Error Tracking

In production, unhandled errors are reported to Sentry:
```python
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=0.1,
    )
```

### Global Exception Handler

All unhandled exceptions return a generic 500 response (no stack traces leaked):
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc} [rid={...}]", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )
```

### Slow Request Warnings

Requests taking longer than 5 seconds are logged:
```python
if elapsed > 5:
    logger.warning(
        f"Slow request: {request.method} {request.url.path} took {elapsed:.2f}s [rid={request_id}]"
    )
```
