# GoTot Admin Guide

Comprehensive guide for administering the GoTot video downloader platform.

---

## Table of Contents

- [Accessing the Admin Panel](#accessing-the-admin-panel)
- [Overview Dashboard](#overview-dashboard)
- [User Management](#user-management)
- [Subscription Management](#subscription-management)
- [Feature Flags](#feature-flags)
- [System Health Monitoring](#system-health-monitoring)
- [Download Analytics](#download-analytics)
- [Affiliate Link Management](#affiliate-link-management)
- [Queue Monitoring](#queue-monitoring)
- [Audit Log Search](#audit-log-search)
- [System Alerts](#system-alerts)

---

## Accessing the Admin Panel

Only user accounts with `is_admin = true` can access admin features.

### Prerequisites

1. Your account must have the `ADMIN` role set in the database.
2. You must be authenticated with a valid JWT bearer token.

### Admin Endpoints

All admin endpoints are prefixed with `/admin/` and require:
- `Authorization: Bearer <token>` header
- An admin-level user account

Access the admin panel at `/admin` in the frontend, or use the API endpoints directly.

---

## Overview Dashboard

**Endpoint:** `GET /admin/stats`

Returns a comprehensive snapshot of platform metrics:

### User Statistics
| Field | Description |
|-------|-------------|
| `users.total` | Total registered users |
| `users.active` | Users with `is_active = true` |
| `users.new_today` | Users registered today |

### Download Statistics
| Field | Description |
|-------|-------------|
| `downloads.total` | All-time downloads |
| `downloads.today` | Downloads today |
| `downloads.unique_ips` | Distinct IP addresses that have downloaded |
| `downloads.by_platform` | Downloads broken down by platform (e.g., `youtube: 5421`, `tiktok: 893`) |

### Revenue Statistics
| Field | Description |
|-------|-------------|
| `revenue.total_usd` | Total revenue from completed payments |
| `revenue.monthly_usd` | Revenue in the last 30 days |
| `revenue.weekly_usd` | Revenue in the last 7 days |

### Subscription Statistics
| Field | Description |
|-------|-------------|
| `subscriptions.active` | Count of active subscriptions |
| `subscriptions.by_plan` | Active subs grouped by plan (pro, unlimited) |

---

## User Management

**Endpoint:** `GET /admin/users`

List and manage all platform users.

### Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `skip` | int | Pagination offset (default: 0) |
| `limit` | int | Results per page (default: 50) |
| `search` | string | Filter by email or username (optional) |

### Response Fields (per user)
| Field | Description |
|-------|-------------|
| `id` | User UUID |
| `email` | Email address |
| `username` | Display name |
| `is_active` | Account active status |
| `is_admin` | Admin role flag |
| `is_verified` | Email verified flag |
| `tier` | Subscription tier (free, pro, unlimited, admin) |
| `daily_downloads` | Downloads used today |
| `total_downloads` | All-time download count |
| `created_at` | Account creation date |

### Ban / Unban a User

**Endpoint:** `POST /admin/users/{user_id}/toggle-ban`

Toggles the `is_active` flag. Banned users cannot log in or use API keys.

- Returns the updated `is_active` status.
- Audit log entry: `ADMIN_TOGGLE_BAN`.

### Delete a User

**Endpoint:** `DELETE /admin/users/{user_id}`

Permanently deletes the user account. Admin users cannot be deleted.

- Audit log entry: `ADMIN_DELETE_USER`.

---

## Subscription Management

**Endpoint:** `GET /admin/subscriptions`

List all subscriptions across the platform.

### Response Fields
| Field | Description |
|-------|-------------|
| `id` | Subscription UUID |
| `user_id` | Owner's user UUID |
| `plan_id` | Tier (pro, unlimited) |
| `status` | active, canceled, past_due, expired |
| `current_period_start` | Billing period start |
| `current_period_end` | Billing period end |
| `created_at` | Subscription creation date |

### Cancel a Subscription

**Endpoint:** `POST /admin/subscriptions/{sub_id}/cancel`

Cancels an active subscription immediately (not just at period end).

- Also cancels at Razorpay to prevent rebilling.
- Audit log entry: `ADMIN_CANCEL_SUBSCRIPTION`.

---

## Feature Flags

Feature flags allow you to toggle platform capabilities without deploying code.

**Endpoint:** `GET /admin/feature-flags`

### Model
| Field | Type | Description |
|-------|------|-------------|
| `key` | string | Unique identifier (e.g., `new_downloader`, `maintenance_mode`) |
| `name` | string | Human-readable name |
| `description` | text | Optional explanation |
| `enabled` | boolean | Whether the feature is active |

### Create a Flag

**Endpoint:** `POST /admin/feature-flags`

Body:
```json
{
  "key": "batch_download_v2",
  "name": "Batch Download v2",
  "description": "New batch download UI with progress indicators",
  "enabled": false
}
```

### Toggle a Flag

**Endpoint:** `PATCH /admin/feature-flags/{flag_id}`

Body:
```json
{
  "enabled": true
}
```

Audit log entry: `ADMIN_CREATE_FEATURE_FLAG` / `ADMIN_TOGGLE_FEATURE_FLAG`.

---

## System Health Monitoring

**Endpoint:** `GET /admin/health/system`

Checks the health of all critical system components.

### Checks Performed

| Component | What's Checked |
|-----------|---------------|
| **Database** | SQL query `SELECT 1` via the async engine |
| **Redis** | `PING` command with 2-second timeout |
| **Environment** | Current environment (development/production) |
| **Version** | Application version (3.0.0) |

### Response Example
```json
{
  "database": "healthy",
  "redis": "healthy",
  "environment": "production",
  "version": "3.0.0"
}
```

---

## Download Analytics

**Endpoint:** `GET /admin/download-analytics`

Parameter: `days` (default: 30, the lookback period)

### Response Fields
| Field | Description |
|-------|-------------|
| `total` | Total downloads in the period |
| `days` | Lookback period |
| `by_platform` | Downloads grouped by platform (e.g., `{"youtube": 15420, "tiktok": 3210}`) |
| `by_format` | Downloads grouped by format (e.g., `{"mp4": 18000, "mp3": 4200}`) |
| `daily` | Array of `{date, count}` for daily trend plotting |

Use this data to:
- Identify which platforms are most popular
- Track format preference trends (video vs audio)
- Monitor daily/weekly download volume

---

## Affiliate Link Management

Affiliate links are promotional URLs displayed on the platform for monetization.

### List Affiliates

**Endpoint:** `GET /admin/affiliates`

### Create an Affiliate

**Endpoint:** `POST /admin/affiliates`

Body:
```json
{
  "platform": "youtube",
  "name": "YouTube Premium",
  "url": "https://yt.be/premium",
  "description": "Ad-free YouTube experience",
  "commission_rate": "10%"
}
```

### Update an Affiliate

**Endpoint:** `PATCH /admin/affiliates/{link_id}`

Supports partial updates. Fields:
- `platform`, `name`, `url`, `description`, `commission_rate`, `is_active`

### Delete an Affiliate

**Endpoint:** `DELETE /admin/affiliates/{link_id}`

Audit log entries: `ADMIN_CREATE_AFFILIATE`, `ADMIN_UPDATE_AFFILIATE`, `ADMIN_DELETE_AFFILIATE`.

---

## Queue Monitoring

**Endpoint:** `GET /admin/queue-status`

Monitors the Celery/async download task queue.

### Response Fields
| Field | Description |
|-------|-------------|
| `total` | Total tasks in the database |
| `pending` | Tasks waiting to be processed |
| `processing` | Tasks currently being downloaded |
| `completed` | Successfully completed tasks |
| `failed` | Tasks that errored out |
| `recent` | Last 10 tasks (id, truncated url, status, created_at) |

### What to Watch
- **High pending count**: Workers may be under-scaled or Redis/Celery may be degraded.
- **Rising failed count**: Platform may be rate-limiting, or downloader may need updates.
- **Recent errors**: Inspect URLs to identify problematic platforms.

---

## Audit Log Search

**Endpoint:** `GET /admin/audit-logs`

Every significant action is logged for security and compliance.

### Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Free-text search across details, resource, email |
| `action` | string | Filter by action type (e.g., `LOGIN_SUCCESS`, `DOWNLOAD`) |
| `skip` | int | Pagination offset |
| `limit` | int | Results per page (max 200) |

### Action Types
| Action | Description |
|--------|-------------|
| `LOGIN_SUCCESS` | Successful user login |
| `LOGIN_FAILED` | Failed login attempt |
| `REGISTER` | New user registration |
| `DOWNLOAD` | Download completed |
| `PAYMENT` | Payment processed |
| `ADMIN_TOGGLE_BAN` | User was banned/unbanned |
| `ADMIN_CANCEL_SUBSCRIPTION` | Subscription canceled by admin |
| `ADMIN_DELETE_USER` | User deleted |
| `ADMIN_CREATE_FEATURE_FLAG` | Feature flag created |
| `ADMIN_TOGGLE_FEATURE_FLAG` | Feature flag toggled |
| `ADMIN_CREATE_AFFILIATE` | Affiliate link created |
| `ADMIN_UPDATE_AFFILIATE` | Affiliate link updated |
| `ADMIN_DELETE_AFFILIATE` | Affiliate link deleted |

---

## System Alerts

**Endpoint:** `GET /admin/system-alerts`

Auto-generated alerts based on system thresholds.

### Alert Triggers
| Condition | Severity | Metric |
|-----------|----------|--------|
| >10 downloads failed in the last hour | warning | `failed_downloads` |
| Failed payments in the last 24 hours | warning | `failed_payments` |
| New users in the last 24 hours | info | `new_users` |

Alerts are generated live — they are not stored in the database.
