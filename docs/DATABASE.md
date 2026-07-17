# GoTot Database Schema

Comprehensive documentation of the GoTot PostgreSQL database schema.

---

## Table of Contents

- [Overview](#overview)
- [Tables](#tables)
  - [users](#users)
  - [download_history](#download_history)
  - [download_tasks](#download_tasks)
  - [subscriptions](#subscriptions)
  - [payments](#payments)
  - [api_keys](#api_keys)
  - [referrals](#referrals)
  - [affiliate_links](#affiliate_links)
  - [ad_impressions](#ad_impressions)
  - [notifications](#notifications)
  - [feature_flags](#feature_flags)
  - [audit_logs](#audit_logs)
- [Entity Relationships](#entity-relationships)
- [Migration Strategy](#migration-strategy)
- [Indexes and Performance](#indexes-and-performance)
- [Enum Types](#enum-types)

---

## Overview

- **Database**: PostgreSQL 16
- **ORM**: SQLAlchemy 2.0 async
- **Driver**: asyncpg
- **Extensions**: `uuid-ossp`, `pgcrypto`
- **Naming**: `snake_case` table and column names
- **Primary keys**: UUID v4 (auto-generated)
- **Timestamps**: UTC datetime

### Connection Pool

```python
engine = create_async_engine(
    settings.database_url,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)
```

---

## Tables

### users

The core user account table. Stores authentication, role, and usage tracking data.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK, default `uuid_generate_v4()` | Unique user identifier |
| `email` | `VARCHAR(255)` | UNIQUE, NOT NULL, INDEX | User email address |
| `username` | `VARCHAR(100)` | UNIQUE, NOT NULL, INDEX | Display name |
| `hashed_password` | `VARCHAR(255)` | NOT NULL | Bcrypt hashed password |
| `role` | `subscription_tier` | NOT NULL, default `'free'` | Subscription tier (free, pro, unlimited, admin) |
| `is_active` | `BOOLEAN` | NOT NULL, default `true` | Account banned/deactivated |
| `is_verified` | `BOOLEAN` | NOT NULL, default `false` | Email verified |
| `is_admin` | `BOOLEAN` | NOT NULL, default `false` | Admin privileges |
| `daily_download_limit` | `INTEGER` | NOT NULL, default `999` | Max downloads per day |
| `downloads_today` | `INTEGER` | NOT NULL, default `0` | Downloads used today |
| `download_credits` | `INTEGER` | NOT NULL, default `0` | Purchased download credits |
| `total_downloads` | `BIGINT` | NOT NULL, default `0` | Lifetime download count |
| `last_download_reset` | `TIMESTAMP` | NOT NULL, default `now()` | Last daily limit reset |
| `refresh_token_version` | `INTEGER` | NOT NULL, default `0` | Incremented on refresh to invalidate old tokens |
| `email_preferences` | `JSON` / `TEXT` | NOT NULL, default `{}` | Email notification preferences |
| `created_at` | `TIMESTAMP` | NOT NULL, default `now()` | Account creation time |
| `updated_at` | `TIMESTAMP` | NOT NULL, default `now()`, ON UPDATE `now()` | Last update time |

**Indexes:**
- `ix_users_email` — UNIQUE on `email`
- `ix_users_username` — UNIQUE on `username`

### download_history

Records every completed download for history, analytics, and audit.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK | Record ID |
| `user_id` | `UUID` | NULLABLE, INDEX | User who downloaded (NULL = anonymous) |
| `url` | `TEXT` | NOT NULL | Source video URL |
| `title` | `VARCHAR(500)` | NULLABLE | Video title |
| `thumbnail_url` | `TEXT` | NULLABLE | Video thumbnail URL |
| `platform` | `VARCHAR(50)` | NOT NULL | Source platform (youtube, tiktok, etc.) |
| `format` | `VARCHAR(20)` | NOT NULL | Downloaded format (mp4, mp3, webm) |
| `status` | `VARCHAR(20)` | NOT NULL, default `'completed'` | Download status |
| `file_size` | `INTEGER` | NULLABLE | File size in bytes |
| `ip_address` | `VARCHAR(45)` | NULLABLE | Downloader's IP address |
| `is_paid` | `BOOLEAN` | NOT NULL, default `false` | Was this a paid download |
| `created_at` | `TIMESTAMP` | NOT NULL, default `now()` | Download timestamp |

**Indexes:**
- `ix_download_history_user_id` on `user_id`

### download_tracks

Tracks async download tasks in the Celery queue.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK | Task ID |
| `user_id` | `UUID` | NULLABLE, INDEX | User who queued the download |
| `url` | `TEXT` | NOT NULL | Source video URL |
| `platform` | `VARCHAR(50)` | NULLABLE | Detected platform |
| `format_id` | `VARCHAR(20)` | NULLABLE | Requested format |
| `status` | `VARCHAR(20)` | NOT NULL, default `'pending'`, INDEX | Current status |
| `progress` | `FLOAT` | NOT NULL, default `0` | Progress percentage (0-100) |
| `error_message` | `TEXT` | NULLABLE | Error details if failed |
| `file_size` | `INTEGER` | NULLABLE | Resulting file size |
| `created_at` | `TIMESTAMP` | NOT NULL, default `now()` | Creation time |
| `updated_at` | `TIMESTAMP` | NOT NULL, default `now()`, ON UPDATE `now()` | Last update time |

**Indexes:**
- `ix_download_tasks_user_id` on `user_id`
- `ix_download_tasks_status` on `status`

### subscriptions

Manages recurring subscription billing via Razorpay.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK | Subscription ID |
| `user_id` | `UUID` | FK → `users.id`, NOT NULL, INDEX | Subscribing user |
| `tier` | `subscription_tier` | NOT NULL | Plan tier (pro, unlimited) |
| `status` | `subscription_status` | NOT NULL, default `'active'` | Current status |
| `razorpay_subscription_id` | `VARCHAR(255)` | NULLABLE, INDEX | Razorpay subscription reference |
| `razorpay_customer_id` | `VARCHAR(255)` | NULLABLE | Razorpay customer reference |
| `current_period_start` | `TIMESTAMP` | NULLABLE | Current billing period start |
| `current_period_end` | `TIMESTAMP` | NULLABLE | Current billing period end |
| `canceled_at` | `TIMESTAMP` | NULLABLE | When subscription was canceled |
| `created_at` | `TIMESTAMP` | NOT NULL, default `now()` | Creation time |
| `updated_at` | `TIMESTAMP` | NOT NULL, default `now()`, ON UPDATE `now()` | Last update time |

**Relationships:**
- `user` → `users.id` (via SQLAlchemy `relationship`)

**Indexes:**
- `ix_subscriptions_user_id` on `user_id`
- `ix_subscriptions_razorpay_subscription_id` on `razorpay_subscription_id`

### payments

Records all payment transactions processed through Razorpay.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK | Payment ID |
| `user_id` | `UUID` | FK → `users.id`, NULLABLE, INDEX | Paying user (NULL = anonymous) |
| `razorpay_payment_id` | `VARCHAR(255)` | NULLABLE, INDEX | Razorpay payment reference |
| `razorpay_order_id` | `VARCHAR(255)` | NULLABLE | Razorpay order reference |
| `amount` | `NUMERIC(10,2)` | NOT NULL | Payment amount |
| `currency` | `VARCHAR(3)` | NOT NULL, default `'USD'` | Currency code |
| `status` | `payment_status` | NOT NULL, default `'pending'` | Payment status |
| `payment_type` | `VARCHAR(50)` | NOT NULL | Type (subscription, pay_per_download) |
| `description` | `VARCHAR(500)` | NULLABLE | Human-readable description |
| `metadata_json` | `TEXT` | NULLABLE | Raw Razorpay notes/metadata |
| `created_at` | `TIMESTAMP` | NOT NULL, default `now()` | Payment timestamp |

**Indexes:**
- `ix_payments_user_id` on `user_id`
- `ix_payments_razorpay_payment_id` on `razorpay_payment_id`

### api_keys

API keys for programmatic access to the download engine.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK | Key ID |
| `user_id` | `UUID` | FK → `users.id`, NOT NULL, INDEX | Key owner |
| `key` | `VARCHAR(64)` | UNIQUE, NOT NULL, INDEX | SHA-256 hash of the raw key |
| `name` | `VARCHAR(100)` | NOT NULL | Human-readable key name |
| `tier` | `subscription_tier` | NOT NULL, default `'free'` | Tier at creation time |
| `requests_count` | `INTEGER` | NOT NULL, default `0` | Total requests made |
| `daily_limit` | `INTEGER` | NOT NULL, default `50` | Max requests per day |
| `is_active` | `BOOLEAN` | NOT NULL, default `true` | Whether key is active |
| `last_used_at` | `TIMESTAMP` | NULLABLE | Last usage timestamp |
| `created_at` | `TIMESTAMP` | NOT NULL, default `now()` | Creation time |
| `expires_at` | `TIMESTAMP` | NULLABLE | Expiration date (NULL = never) |

**Relationships:**
- `user` → `users.id`

**Indexes:**
- `ix_api_keys_user_id` on `user_id`
- `ix_api_keys_key` — UNIQUE on `key`

### referrals

Tracks referral relationships between users.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK | Referral record ID |
| `referrer_id` | `UUID` | FK → `users.id`, NOT NULL, INDEX | User who shared the code |
| `referred_id` | `UUID` | FK → `users.id`, NULLABLE, INDEX | User who used the code |
| `referral_code` | `VARCHAR(20)` | UNIQUE, NOT NULL, INDEX | Unique code (e.g., `GOTOTABC123`) |
| `status` | `VARCHAR(20)` | NOT NULL, default `'pending'` | pending / completed |
| `reward_credits` | `INTEGER` | NOT NULL, default `0` | Downloads credited to referrer |
| `referred_email` | `VARCHAR(255)` | NULLABLE | Email of referred user |
| `created_at` | `TIMESTAMP` | NOT NULL, default `now()` | When code was generated |
| `completed_at` | `TIMESTAMP` | NULLABLE | When referral was completed |

**Indexes:**
- `ix_referrals_referrer_id` on `referrer_id`
- `ix_referrals_referred_id` on `referred_id`
- `ix_referrals_referral_code` — UNIQUE on `referral_code`

### affiliate_links

Affiliate marketing links displayed on the platform.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK | Link ID |
| `platform` | `VARCHAR(50)` | NOT NULL | Related platform (youtube, tiktok) |
| `name` | `VARCHAR(200)` | NOT NULL | Display name |
| `url` | `TEXT` | NOT NULL | Affiliate URL |
| `description` | `TEXT` | NULLABLE | Link description |
| `commission_rate` | `VARCHAR(10)` | NULLABLE | e.g., "10%" |
| `is_active` | `BOOLEAN` | NOT NULL, default `true` | Whether link is shown |
| `clicks` | `BIGINT` | NOT NULL, default `0` | Click counter |
| `created_at` | `TIMESTAMP` | NOT NULL, default `now()` | Creation time |

### ad_impressions

Tracks ad view events for optional ad-supported model.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK | Impression ID |
| `user_id` | `UUID` | FK → `users.id`, NULLABLE | User (NULL = anonymous) |
| `ad_type` | `VARCHAR(50)` | NOT NULL | Type of ad |
| `ip_address` | `VARCHAR(45)` | NULLABLE | Viewer IP |
| `watched_seconds` | `INTEGER` | NOT NULL, default `0` | Seconds watched |
| `completed` | `BOOLEAN` | NOT NULL, default `false` | Ad completed |
| `reward_granted` | `BOOLEAN` | NOT NULL, default `false` | Reward given |
| `created_at` | `TIMESTAMP` | NOT NULL, default `now()` | Impression timestamp |

### notifications

In-app and email notification records.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK | Notification ID |
| `user_id` | `UUID` | NOT NULL, INDEX | Recipient user |
| `type` | `notification_type` | NOT NULL | Notification category |
| `title` | `VARCHAR(200)` | NOT NULL | Notification title |
| `message` | `TEXT` | NOT NULL | Notification body |
| `data` | `JSON` | NULLABLE | Additional structured data |
| `is_read` | `BOOLEAN` | NOT NULL, default `false` | Read status |
| `is_push_sent` | `BOOLEAN` | NOT NULL, default `false` | Push notification sent |
| `is_email_sent` | `BOOLEAN` | NOT NULL, default `false` | Email sent |
| `created_at` | `TIMESTAMP` | NOT NULL, default `now()` | Creation time |
| `read_at` | `TIMESTAMP` | NULLABLE | When it was read |

**Indexes:**
- `ix_notifications_user_id` on `user_id`

### feature_flags

Toggleable platform features without code deployment.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK | Flag ID |
| `key` | `VARCHAR(100)` | UNIQUE, NOT NULL, INDEX | Machine-readable key |
| `name` | `VARCHAR(200)` | NOT NULL | Human-readable name |
| `description` | `TEXT` | NULLABLE | What this flag controls |
| `enabled` | `BOOLEAN` | NOT NULL, default `false` | Whether feature is active |
| `created_at` | `TIMESTAMP` | NOT NULL, default `now()` | Creation time |
| `updated_at` | `TIMESTAMP` | NOT NULL, default `now()`, ON UPDATE `now()` | Last toggle time |

**Indexes:**
- `ix_feature_flags_key` — UNIQUE on `key`

### audit_logs

Structured audit trail for security and compliance.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK | Log entry ID |
| `action` | `VARCHAR(50)` | NOT NULL, INDEX | Action type (e.g., LOGIN_SUCCESS, DOWNLOAD) |
| `user_id` | `UUID` | NULLABLE, INDEX | Acting user |
| `email` | `VARCHAR(255)` | NULLABLE | User email at time of action |
| `ip_address` | `VARCHAR(45)` | NULLABLE | Request IP address |
| `resource` | `VARCHAR(500)` | NULLABLE | Affected resource |
| `details` | `JSON` / `TEXT` | NOT NULL, default `{}` | Action-specific details |
| `status` | `VARCHAR(20)` | NOT NULL, default `'success'` | success / failed |
| `created_at` | `TIMESTAMP` | NOT NULL, default `now()` | Event timestamp |

**Indexes:**
- `ix_audit_logs_action` on `action`
- `ix_audit_logs_user_id` on `user_id`

---

## Entity Relationships

```
users
├── 1:N → download_history (user_id)
├── 1:N → download_tasks (user_id)
├── 1:1 → subscriptions (user_id)
├── 1:N → payments (user_id)
├── 1:N → api_keys (user_id)
├── 1:N → referrals (referrer_id)
├── 1:N → referrals (referred_id)
├── 1:N → ad_impressions (user_id)
├── 1:N → notifications (user_id)
└── 1:N → audit_logs (user_id)

subscriptions
└── N:1 → users (user_id)

payments
└── N:1 → users (user_id)

api_keys
└── N:1 → users (user_id)

referrals
├── N:1 → users (referrer_id)
└── N:1 → users (referred_id)

ad_impressions
└── N:1 → users (user_id)

notifications
└── N:1 → users (user_id)

audit_logs
└── N:1 → users (user_id)

No relationships:
- feature_flags (standalone)
- affiliate_links (standalone)
```

---

## Migration Strategy

### Tool: Alembic

GoTot uses Alembic for schema migrations with async PostgreSQL support.

### Migration Location

```
backend/alembic/
├── env.py               # Async migration environment
├── script.py.mako       # Migration template
└── versions/            # Migration scripts
    └── 001_initial_schema.py
```

### Workflow

```bash
# Auto-generate migration from model changes
cd backend
alembic revision --autogenerate -m "description of change"

# Review the generated migration file
# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# View history
alembic history

# Check current version
alembic current
```

### Migration Best Practices

1. **Always review auto-generated migrations** — autogenerate may miss some changes or produce incorrect SQL.
2. **Test on a staging database** before applying to production.
3. **Use `batch` operations** for large table changes to avoid locks.
4. **Include both `upgrade()` and `downgrade()`** functions.
5. **Never edit existing migrations** — create a new migration file.
6. **Version control all migration files**.

### Initial Migration

The initial migration (`001_initial_schema.py`) was created from the existing model definitions and includes all 12 tables plus enum types.

---

## Indexes and Performance

### Current Indexes

| Table | Index | Type | Purpose |
|-------|-------|------|---------|
| `users` | `ix_users_email` | UNIQUE | Login by email |
| `users` | `ix_users_username` | UNIQUE | Username uniqueness check |
| `download_history` | `ix_download_history_user_id` | B-tree | User history queries |
| `download_tasks` | `ix_download_tasks_user_id` | B-tree | User task queries |
| `download_tasks` | `ix_download_tasks_status` | B-tree | Queue status aggregation |
| `subscriptions` | `ix_subscriptions_user_id` | B-tree | User subscription lookup |
| `subscriptions` | `ix_subscriptions_razorpay_subscription_id` | B-tree | Razorpay webhook matching |
| `payments` | `ix_payments_user_id` | B-tree | User payment history |
| `payments` | `ix_payments_razorpay_payment_id` | B-tree | Razorpay webhook matching |
| `api_keys` | `ix_api_keys_user_id` | B-tree | User key listing |
| `api_keys` | `ix_api_keys_key` | UNIQUE | Key lookup for auth |
| `referrals` | `ix_referrals_referrer_id` | B-tree | Referral stats/queries |
| `referrals` | `ix_referrals_referred_id` | B-tree | Referral lookup |
| `referrals` | `ix_referrals_referral_code` | UNIQUE | Code application lookup |
| `notifications` | `ix_notifications_user_id` | B-tree | User notification queries |
| `feature_flags` | `ix_feature_flags_key` | UNIQUE | Flag lookup |
| `audit_logs` | `ix_audit_logs_action` | B-tree | Audit search by action |
| `audit_logs` | `ix_audit_logs_user_id` | B-tree | Audit search by user |

### Query Patterns

| Pattern | Table | Index Used | Frequency |
|---------|-------|------------|-----------|
| Login by email | `users` | `ix_users_email` | High |
| User download history | `download_history` | `ix_download_history_user_id` | Medium |
| User subscriptions | `subscriptions` | `ix_subscriptions_user_id` | Low |
| Active subscription count | `subscriptions` | (seq scan on status) | Low (admin) |
| Platform analytics | `download_history` | (seq scan on platform) | Low (admin) |
| Audit search | `audit_logs` | `ix_audit_logs_action` | Low (admin) |
| API key auth | `api_keys` | `ix_api_keys_key` | Medium |
| Referral code lookup | `referrals` | `ix_referrals_referral_code` | Low |

### Performance Recommendations

1. **Composite indexes**: For admin analytics queries, consider composite indexes:
   ```sql
   CREATE INDEX ix_download_history_platform_created ON download_history(platform, created_at);
   ```

2. **Partial indexes**: For active subscriptions:
   ```sql
   CREATE INDEX ix_subscriptions_active ON subscriptions(user_id) WHERE status = 'active';
   ```

3. **Table partitioning**: For `download_history` and `audit_logs` at scale (millions+ rows), consider partitioning by `created_at`.

4. **Regular maintenance**:
   ```sql
   VACUUM ANALYZE;
   REINDEX TABLE download_history;
   ```

---

## Enum Types

### subscription_tier

```sql
CREATE TYPE subscription_tier AS ENUM (
    'free',
    'pro',
    'unlimited',
    'admin'
);
```

Used in: `users.role`, `subscriptions.tier`, `api_keys.tier`

### subscription_status

```sql
CREATE TYPE subscription_status AS ENUM (
    'active',
    'canceled',
    'past_due',
    'expired'
);
```

Used in: `subscriptions.status`

### payment_status

```sql
CREATE TYPE payment_status AS ENUM (
    'pending',
    'completed',
    'failed',
    'refunded'
);
```

Used in: `payments.status`

### notification_type

```sql
CREATE TYPE notification_type AS ENUM (
    'download_complete',
    'download_failed',
    'subscription_expiring',
    'payment_received',
    'payment_failed',
    'referral_reward',
    'security_alert',
    'admin_announcement',
    'plan_upgrade',
    'welcome'
);
```

Used in: `notifications.type`
