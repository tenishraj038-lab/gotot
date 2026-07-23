# Security Report

## Authentication

| Area | Status | Details |
|------|--------|---------|
| Login | ✅ Fixed | `user.role.value` crash resolved; refresh token body format fixed |
| Registration | ✅ Fixed | `.value` crash on role field fixed |
| Logout | ✅ Working | Frontend clears tokens from localStorage |
| Email OTP | ✅ Working | JWT-based email verification with 24h expiry |
| Google Sign-In | ✅ Working | Token verification via Google's tokeninfo endpoint |
| Password Reset | ✅ Working | JWT-based reset with 1h expiry, email sent via SMTP |
| Session Handling | ✅ Fixed | `refresh_token_version` now committed to DB |
| Refresh Tokens | ✅ Fixed | Backend accepts JSON body, version checking works |
| JWT Validation | ✅ Working | HS256, expiry checking, token type validation |
| Cookie Security | ✅ Fixed | `httponly`, `samesite=lax`, `secure` in production |
| Protected Routes | ✅ Working | Bearer token extraction, `/me`, payments, admin |
| User Roles | ✅ Fixed | String comparison works without enum `.value` crash |
| Admin Roles | ✅ Fixed | `is_admin` check works on all admin routes |

## Security Headers

| Header | Value |
|--------|-------|
| X-Content-Type-Options | nosniff |
| X-Frame-Options | DENY |
| X-XSS-Protection | 1; mode=block |
| Strict-Transport-Security | max-age=31536000; includeSubDomains; preload |
| Referrer-Policy | strict-origin-when-cross-origin |
| Permissions-Policy | camera=(), microphone=(), geolocation=() |
| Cross-Origin-Resource-Policy | same-origin |
| Cross-Origin-Opener-Policy | same-origin |
| Cross-Origin-Embedder-Policy | require-corp |
| CSP (production) | default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://checkout.razorpay.com https://www.googletagmanager.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; img-src 'self' data: https: blob:; font-src 'self' https://fonts.gstatic.com; connect-src 'self' https://api.razorpay.com https://sentry.io; frame-src 'self' https://checkout.razorpay.com; media-src 'self'; object-src 'none' |

## CSRF Protection
- **Middleware**: Active in production. Validates `X-CSRF-Token` header against cookie.
- **Exempt paths**: /health, /contact, /auth/register, /auth/login, /auth/refresh, /api-keys/create
- **Auth bypass**: Requests with valid Bearer token or API key skip CSRF check.
- **Frontend**: CSRF token now sent for non-Bearer mutating requests.

## Rate Limiting
- **Strategy**: SlowAPI with Redis backend
- **Default limit**: Configurable via `RATE_LIMIT_PER_MINUTE` (default: 60)
- **Per route**: Can be overridden with `@limiter.limit()` decorator

## SQL Injection Prevention
- SQLAlchemy ORM with parameterized queries throughout
- `search_downloads` sanitizes user input (`re.sub(r'[\\%_]', '', q)`) before LIKE query
- No raw SQL string concatenation

## Audit Logging
- All login attempts (success/failure), registrations, downloads, payments, admin actions logged
- Logs go to structured JSON and AuditLog DB table

## Remaining Concerns
- CSRF middleware only active in production — dev environment has no CSRF protection
- Google token verification uses `tokeninfo` endpoint (no `sub` validation against client ID)
