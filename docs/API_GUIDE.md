# GoTot API Guide

Comprehensive API documentation for the GoTot universal video downloader platform.

**Base URL:** `https://gotot.app/api` (production) or `http://localhost:8000` (development)

**Version:** 3.0.0

---

## Table of Contents

- [Authentication](#authentication)
- [Rate Limits](#rate-limits)
- [Error Codes](#error-codes)
- [Endpoints](#endpoints)
  - [Auth](#auth)
  - [Downloads](#downloads)
  - [Payments](#payments)
  - [API Keys](#api-keys)
  - [Referrals](#referrals)
  - [Admin](#admin)
  - [Notifications](#notifications)
  - [Contact](#contact)
  - [Affiliates](#affiliates)
  - [WebSocket](#websocket)
- [Code Examples](#code-examples)
- [Webhook Documentation](#webhook-documentation)

---

## Authentication

### JWT Bearer Tokens

Most endpoints require authentication via a Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

### Token Types

| Token | Lifetime | Usage |
|-------|----------|-------|
| `access_token` | 60 minutes | API authentication |
| `refresh_token` | 30 days | Obtain new access tokens |

### Refresh Token Rotation

When a refresh token is used, the old token is invalidated and a new pair is issued. If a compromised refresh token is used after rotation, all sessions are revoked.

### API Key Authentication

API keys can be used instead of JWT for download endpoints:

```
X-API-Key: gt_abc123...
```

---

## Rate Limits

Limits are applied per IP address or per API key, measured in requests per minute.

| Tier | Rate Limit |
|------|-----------|
| Anonymous (unauthenticated) | 60 req/min |
| Free (authenticated) | 60 req/min |
| Pro | 120 req/min |
| Unlimited | 300 req/min |

When exceeded, the API returns `429 Too Many Requests`.

---

## Error Codes

| Code | Description |
|------|-------------|
| `400` | Bad request — invalid input, validation error |
| `401` | Unauthorized — missing or invalid token |
| `403` | Forbidden — insufficient permissions, CSRF failure, banned account |
| `404` | Resource not found |
| `409` | Conflict — duplicate resource (email, username, feature flag key) |
| `429` | Rate limit exceeded |
| `500` | Internal server error |
| `502` | External service failure (Google auth verification) |
| `503` | Service unavailable (Google auth not configured) |

Error response format:
```json
{
  "detail": "Descriptive error message"
}
```

---

## Endpoints

---

### Auth

#### Register

Creates a new user account and returns tokens.

```
POST /auth/register
```

**Request:**
```json
{
  "email": "user@example.com",
  "username": "myusername",
  "password": "MyPassword1"
}
```

**Validation:**
- `email`: Must contain `@` and a valid domain
- `username`: 3+ alphanumeric characters
- `password`: 8+ characters, must contain uppercase letter and digit

**Response** (201):
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

#### Login

```
POST /auth/login
```

**Request:**
```json
{
  "email": "user@example.com",
  "password": "MyPassword1"
}
```

**Response:** Same as register.

#### Refresh Token

Rotates the token pair. Previous refresh token is invalidated.

```
POST /auth/refresh
```

**Request:** Send raw `refresh_token` string as the body:
```
eyJhbGci...
```

**Response:** New `access_token` and `refresh_token`.

#### Get Current User

```
GET /auth/me
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "myusername",
  "role": "free",
  "is_active": true,
  "is_admin": false,
  "daily_download_limit": 999,
  "downloads_today": 3,
  "download_credits": 0,
  "total_downloads": 42,
  "email_preferences": {},
  "created_at": "2026-01-15T10:30:00"
}
```

Note: `downloads_today` is auto-reset at midnight UTC.

#### Update Profile

```
PUT /auth/me
```

**Request:**
```json
{
  "username": "newusername",
  "email_preferences": {
    "security_alerts": true,
    "product_updates": false,
    "marketing": false
  }
}
```

Both fields are optional.

#### Change Password

```
POST /auth/change-password
```

**Request:**
```json
{
  "current_password": "OldPass1",
  "new_password": "NewPass1"
}
```

Password requirements: 8+ chars, uppercase letter, digit.

#### Google Login

```
POST /auth/google/login
```

**Request:**
```json
{
  "id_token": "google-id-token-here"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "is_new_user": false
}
```

---

### Downloads

#### Get Video Info

Analyzes a video URL and returns available formats without downloading.

```
POST /download/info
```

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

**Response:**
```json
{
  "title": "Rick Astley - Never Gonna Give You Up",
  "platform": "youtube",
  "duration": 212,
  "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
  "formats": [
    {
      "format_id": "137",
      "ext": "mp4",
      "resolution": "1920x1080",
      "height": 1080,
      "filesize": 52428800,
      "filesize_approx": 52428800,
      "filesize_human": "50.0 MB",
      "vcodec": "avc1.640028",
      "acodec": "none",
      "fps": 30,
      "abr": 0,
      "tbr": 2500,
      "quality_label": "MP4 1080p",
      "has_video": true,
      "has_audio": false,
      "type": "video_only"
    }
  ],
  "is_playlist": false,
  "playlist_count": 0,
  "requires_payment": false
}
```

#### Start Download

Downloads a video and returns a direct download URL.

```
POST /download/start
```

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "format_id": "137+140",
  "as_mp3": false,
  "mp3_bitrate": "192"
}
```

**Response:**
```json
{
  "file_name": "Rick_Astley_Never_Gonna_Give_You_Up",
  "file_size": 52428800,
  "format": "mp4",
  "download_url": "/download/file/abc123.mp4",
  "title": "Rick Astley - Never Gonna Give You Up",
  "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
}
```

**Note:** Download URLs expire after 1 hour (file retention policy).

#### Batch Download

Downloads up to 20 URLs at once.

```
POST /download/batch
```

**Request:**
```json
{
  "urls": [
    "https://youtube.com/watch?v=...",
    "https://tiktok.com/@user/video/..."
  ],
  "format_id": "best",
  "as_mp3": false
}
```

**Response:**
```json
{
  "results": [
    {
      "url": "https://youtube.com/watch?v=...",
      "status": "completed",
      "file_name": "video_title",
      "file_size": 12345678,
      "download_url": "/download/file/abc.mp4"
    },
    {
      "url": "https://tiktok.com/@user/video/...",
      "status": "error",
      "detail": "Could not extract info"
    }
  ],
  "total": 2,
  "successful": 1
}
```

#### Playlist Info

Returns all entries in a playlist.

```
POST /download/playlist
```

**Request:**
```json
{
  "url": "https://www.youtube.com/playlist?list=PL..."
}
```

**Response:**
```json
{
  "entries": [
    {
      "url": "https://youtube.com/watch?v=...",
      "title": "Video 1",
      "duration": 180,
      "thumbnail": "https://i.ytimg.com/vi/.../hqdefault.jpg"
    }
  ],
  "total": 25
}
```

#### Queue Download

Adds a download to the Celery queue for background processing.

```
POST /download/queue
```

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "format_id": "best",
  "as_mp3": false,
  "mp3_bitrate": "192"
}
```

**Response:**
```json
{
  "task_id": "uuid",
  "status": "queued",
  "message": "Download queued successfully",
  "ws_url": "/ws/progress/uuid"
}
```

#### Queue Status

```
GET /download/queue/{task_id}
```

**Response:**
```json
{
  "task_id": "uuid",
  "status": "downloading",
  "progress": 45,
  "message": "Downloading video..."
}
```

#### Download History

```
GET /download/history?skip=0&limit=20
```

Requires authentication. Returns authenticated user's download history.

#### Search History

```
GET /download/search?q=rick
```

Requires authentication. Searches download history by URL.

#### Serve File

```
GET /download/file/{filename}
```

Requires authentication. Returns the file as a download attachment with appropriate `Content-Disposition` and `Content-Type` headers.

#### Recent Downloads (Public)

```
GET /download/recent?limit=10
```

Returns recent downloads with platform, format, size, and time (no URLs or user data).

#### Subtitles

```
POST /download/subtitles
```

**Request:** `{"url": "..."}`

Returns available subtitles for the video (VTT, SRT, TTML formats).

#### Thumbnail

```
POST /download/thumbnail
```

**Request:** `{"url": "..."}`

Returns the video's thumbnail URL.

---

### Payments

All payment endpoints require authentication unless noted.

#### Create Subscription Checkout

```
POST /payment/create-subscription
```

**Request:**
```json
{
  "tier": "pro"
}
```

Valid tiers: `pro`, `unlimited`.

**Response:**
```json
{
  "checkout_url": "https://rzp.io/i/abc123"
```

#### Pay-Per-Download Checkout

Creates a one-time payment link for downloads.

```
POST /payment/pay-per-download
```

**Request:**
```json
{
  "email": "user@example.com"
}
```

Email is optional. If no user is authenticated, this creates an anonymous payment link.

**Response:**
```json
{
  "checkout_url": "https://rzp.io/i/xyz789"
}
```

#### Subscription Status

```
GET /subscription/status
```

**Response:**
```json
{
  "tier": "pro",
  "is_active": true,
  "current_period_end": "2026-05-20T10:00:00",
  "features": {
    "batch_download": true,
    "mp3_conversion": true,
    "api_access": true,
    "no_ads": true,
    "concurrent_downloads": 3
  },
  "daily_downloads": 100,
  "max_quality": "4k"
}
```

#### Cancel Subscription

```
POST /subscription/cancel
```

Cancels at both GoTot and Razorpay. Subscription remains active until period end.

#### Payment History

```
GET /payment/history?skip=0&limit=20
```

#### Payment Webhook

```
POST /payment/webhook
```

**Headers:** `X-Razorpay-Signature: <hmac_sha256_signature>`

See [Webhook Documentation](#webhook-documentation) for details.

---

### API Keys

All API key endpoints require authentication.

#### Create API Key

```
POST /api-keys/create
```

**Request:**
```json
{
  "name": "My CLI Tool"
}
```

Free users can create up to 2 API keys. Pro/Unlimited users have no limit.

**Response:**
```json
{
  "id": "uuid",
  "name": "My CLI Tool",
  "key": "gt_abc123def456...",
  "daily_limit": 50,
  "created_at": "2026-03-15T10:30:00"
}
```

**Important:** The full key is only shown once. Store it securely.

#### List API Keys

```
GET /api-keys/list
```

Returns keys with masked prefixes (e.g., `gt_abc123...`).

#### Revoke API Key

```
POST /api-keys/{key_id}/revoke
```

Immediately deactivates the key.

---

### Referrals

All referral endpoints require authentication.

#### Get My Referral Code

```
GET /referrals/my-code
```

Auto-generates a referral code if one doesn't exist.

**Response:**
```json
{
  "code": "GOTOTABC123",
  "referral_url": "https://gotot.app?ref=GOTOTABC123",
  "total_referred": 5,
  "reward_per_referral": "+3 free downloads"
}
```

#### Apply Referral Code

```
POST /referrals/apply
```

**Request:**
```json
{
  "code": "GOTOTXYZ789"
}
```

**Rules:**
- Cannot use your own code
- Code can only be used once
- Both referrer and referee receive +3 bonus downloads

#### Referral Stats

```
GET /referrals/stats
```

**Response:**
```json
{
  "code": "GOTOTABC123",
  "total_referred": 5,
  "this_week": 1,
  "this_month": 2,
  "pending": 1,
  "total_credits": 15,
  "rank": 42,
  "badge": "top50",
  "reward_per_referral": 3
}
```

#### Referral Leaderboard

```
GET /referrals/leaderboard?period=all_time&limit=50
```

Period options: `global`, `weekly`, `monthly`, `all_time`.

#### Referral History

```
GET /referrals/history?skip=0&limit=20
```

---

### Admin

All admin endpoints require authentication with an admin account.

#### Stats

```
GET /admin/stats
```

Returns platform-wide statistics (users, downloads, revenue, subscriptions).

#### List Users

```
GET /admin/users?skip=0&limit=50&search=user@example.com
```

#### Toggle User Ban

```
POST /admin/users/{user_id}/toggle-ban
```

#### Delete User

```
DELETE /admin/users/{user_id}
```

#### List Subscriptions

```
GET /admin/subscriptions?skip=0&limit=50
```

#### Cancel Subscription

```
POST /admin/subscriptions/{sub_id}/cancel
```

#### Feature Flags

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/admin/feature-flags` | List all flags |
| `POST` | `/admin/feature-flags` | Create a flag |
| `PATCH` | `/admin/feature-flags/{id}` | Toggle a flag |

#### System Health

```
GET /admin/health/system
```

#### Queue Status

```
GET /admin/queue-status
```

#### Audit Logs

```
GET /admin/audit-logs?query=&action=&skip=0&limit=50
```

#### System Alerts

```
GET /admin/system-alerts
```

#### Download Analytics

```
GET /admin/download-analytics?days=30
```

#### Affiliate Links

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/admin/affiliates` | List all |
| `POST` | `/admin/affiliates` | Create |
| `PATCH` | `/admin/affiliates/{id}` | Update |
| `DELETE` | `/admin/affiliates/{id}` | Delete |

---

### Notifications

All notification endpoints require authentication.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/notifications/` | List notifications |
| `GET` | `/notifications/unread-count` | Get unread count |
| `POST` | `/notifications/{id}/read` | Mark one as read |
| `POST` | `/notifications/read-all` | Mark all as read |

Notification parameters: `skip`, `limit`, `unread_only` (boolean).

---

### Contact

```
POST /contact
```

**Request:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "message": "I have a question about..."
}
```

Validates: name (2+ chars), email (valid format), message (10-2000 chars).

---

### Affiliates (Public)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/affiliates/links` | List active affiliate links |
| `POST` | `/affiliates/{id}/click` | Record a click |

---

### WebSocket

#### Download Progress

```
WebSocket /ws/progress/{task_id}
```

Connects to a task-specific channel that publishes real-time progress updates via Redis pub/sub.

**Message format:**
```json
{
  "task_id": "uuid",
  "status": "downloading",
  "progress": 45,
  "message": "Downloading video...",
  "updated_at": "2026-03-15T10:30:00"
}
```

Status progression: `queued` → `downloading` → `processing` → `completed` (or `error`).

---

## Code Examples

### curl

```bash
# Get video info
curl -X POST https://gotot.app/api/download/info \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Start download (authenticated)
curl -X POST https://gotot.app/api/download/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGci..." \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "format_id": "best"}'

# Register new user
curl -X POST https://gotot.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "username": "myuser", "password": "MyPassword1"}'

# Login
curl -X POST https://gotot.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "MyPassword1"}'

# Refresh token
curl -X POST https://gotot.app/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '"eyJhbGci..."'

# Use API key
curl -X POST https://gotot.app/api/download/info \
  -H "Content-Type: application/json" \
  -H "X-API-Key: gt_abc123..." \
  -d '{"url": "https://www.tiktok.com/@user/video/123"}'

# Get admin stats
curl -X GET https://gotot.app/api/admin/stats \
  -H "Authorization: Bearer eyJhbGci..."
```

### Python

```python
import httpx

BASE_URL = "https://gotot.app/api"

# Register
response = httpx.post(f"{BASE_URL}/auth/register", json={
    "email": "user@example.com",
    "username": "myuser",
    "password": "MyPassword1"
})
tokens = response.json()
access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]

# Get video info
headers = {"Authorization": f"Bearer {access_token}"}
response = httpx.post(
    f"{BASE_URL}/download/info",
    json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    headers=headers,
)
info = response.json()
print(f"Title: {info['title']}")
print(f"Formats: {len(info['formats'])} available")

# Start download
response = httpx.post(
    f"{BASE_URL}/download/start",
    json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "format_id": "best"},
    headers=headers,
)
result = response.json()
print(f"Download: {result['download_url']}")

# Using API key instead
api_headers = {"X-API-Key": "gt_abc123..."}
response = httpx.post(
    f"{BASE_URL}/download/info",
    json={"url": "https://tiktok.com/@user/video/123"},
    headers=api_headers,
)
```

### JavaScript

```javascript
const BASE_URL = "/api";  // or "https://gotot.app/api"

async function getVideoInfo(url, token) {
  const response = await fetch(`${BASE_URL}/download/info`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }

  return response.json();
}

async function downloadVideo(url, formatId, token) {
  const response = await fetch(`${BASE_URL}/download/start`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ url, format_id: formatId }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }

  return response.json();
}

// Usage
const { access_token } = await (
  await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: "user@example.com", password: "MyPassword1" }),
  })
).json();

const info = await getVideoInfo("https://youtube.com/watch?v=dQw4w9WgXcQ", access_token);
console.log(info.title);
```

---

## Webhook Documentation

GoTot receives webhooks from Razorpay to process payment events.

### Endpoint

```
POST /payment/webhook
```

### Headers

| Header | Required | Description |
|--------|----------|-------------|
| `X-Razorpay-Signature` | Yes | HMAC-SHA256 signature for payload verification |

### Webhook Events

| Event | Description | Handler Action |
|-------|-------------|----------------|
| `payment.captured` | One-time payment completed | Adds download credits to user account |
| `subscription.charged` | Recurring subscription payment | Activates or renews subscription |
| `subscription.cancelled` | Subscription cancelled by user/Razorpay | Downgrades user to Free tier |

### Signature Verification

The signature is verified using the Razorpay webhook secret:
```python
expected = hmac.new(
    webhook_secret.encode(),
    request_body,
    hashlib.sha256,
).hexdigest()
assert hmac.compare_digest(expected, signature)
```

### Retry Logic

Razorpay will retry failed webhook deliveries with exponential backoff. Ensure your endpoint responds quickly (ideally < 2 seconds) with a `200` status.

### Security Notes

- Always verify the `X-Razorpay-Signature` header before processing.
- Use the raw request body (not parsed JSON) for signature verification.
- The webhook endpoint is not rate-limited but should reject invalid signatures with `400`.
