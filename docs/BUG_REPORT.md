# GoToT Bug Report

## Critical Bugs (Fixed)

### 1. `backend/app/routes/auth.py:112` - `user.role.value` AttributeError
- **Severity**: CRITICAL - application crash
- **Root cause**: `User.role` is a SQLAlchemy `String` column, not a Python `SubscriptionTier` enum. Calling `.value` on a string raises `AttributeError`.
- **Fix**: Changed `user.role.value` to `user.role` (the string value is already correct).

### 2. `backend/app/routes/auth.py:94` - Wrong audit event on register
- **Severity**: MEDIUM
- **Root cause**: Register endpoint used `audit_logger.log("PASSWORD_CHANGE", ...)` instead of `audit_logger.register(...)`.
- **Fix**: Changed to `audit_logger.register(str(user.id), user.email, ip)`.

### 3. `backend/app/routes/auth.py:367` - Wrong audit event on change_password
- **Severity**: MEDIUM
- **Root cause**: Change password endpoint used `audit_logger.register(...)` instead of `audit_logger.log("PASSWORD_CHANGE", ...)`.
- **Fix**: Corrected the audit event type.

### 4. `backend/app/routes/admin.py:381-384` - Dead query + no cascade delete
- **Severity**: HIGH - user deletion silently fails and orphans child records
- **Root cause**: `await db.execute(select(DownloadHistory).where(...))` is a SELECT, never executes the delete. No cascade deletion of child records (subscriptions, payments, API keys, referrals).
- **Fix**: Replaced with proper `__table__.delete()` calls for all child tables before deleting the user.

### 5. `backend/app/routes/download.py:23` - Duplicate import removed without relinking
- **Severity**: CRITICAL - `generate_task_id` import was removed but still used at line 434.
- **Root cause**: When removing the duplicate import line, the single valid import was also lost.
- **Fix**: Added `generate_task_id` to the remaining import from `app.utils.helpers`.

### 6. `backend/app/middleware/csrf.py` - Fragile Bearer token validation
- **Severity**: LOW - potential false CSRF rejection for short tokens
- **Root cause**: Used `len(auth_header) > 20` as heuristic for valid JWT. JWT tokens with 2 or fewer segments matched this.
- **Fix**: Changed to validate token structure (must have exactly 2 dots and length > 20).

### 7. `backend/app/middleware/csrf.py` - Missing exempt paths
- **Severity**: MEDIUM
- **Root cause**: Several auth and webhook endpoints were missing from `CSRF_EXEMPT_PATHS`, causing CSRF rejection on `/auth/forgot-password`, `/auth/reset-password`, `/auth/verify-email`, `/auth/google/login`, and `/payment/webhook`.
- **Fix**: Added all missing exempt paths.

### 8. `frontend/src/lib/api.ts` - Admin API response type mismatches
- **Severity**: MEDIUM - frontend admin page would crash with `Cannot read properties of undefined`
- **Root cause**: `/admin/users` returns `{ users: [...], total: N }` but frontend expected a bare array. `/admin/stats` returned nested objects but frontend expected flat fields.
- **Fix**: Wrapped admin endpoints in async functions that extract the correct response shape. Added flat fields to backend `/admin/stats` response.

### 9. `backend/app/routes/api_keys.py:55` - SubscriptionTier() crash for unknown role
- **Severity**: MEDIUM
- **Root cause**: `SubscriptionTier(user.role)` raises `ValueError` for unknown role strings.
- **Fix**: Added try/except with fallback to `SubscriptionTier.FREE`.

### 10. `docker-compose.yml` - Celery workers used wrong image
- **Severity**: HIGH - celery_worker and celery_beat containers would fail at startup
- **Root cause**: Used `image: gotot-backend:latest` instead of building from context, and no `build` section was configured.
- **Fix**: Changed to `build: context: ./backend dockerfile: Dockerfile`.

### 11. `backend/app/routes/feedback.py` - get_current_user dependency blocks anonymous users
- **Severity**: HIGH - all feedback/bug-report endpoints crash for anonymous users
- **Root cause**: `get_current_user` raises HTTPException(401) on missing auth, but feedback forms must work without login.
- **Fix**: Created `get_user_optional` dependency that returns `None` for unauthenticated requests.

### 12. `backend/app/routes/download.py:488` - Search endpoint leaks across users
- **Severity**: HIGH - security issue, any user can search all other users' download history
- **Root cause**: The search query had no `user_id` filter.
- **Fix**: Added `DownloadHistory.user_id == user.id` to the WHERE clause.

## Verified
- All 74 tests pass (6 skipped as they require Postgres/Redis).
