# GoTot API Documentation

## Base URL

```
Development: http://localhost:8000
Production:  https://your-domain.com/api
```

## Authentication

Most endpoints support optional authentication via Bearer tokens:

```
Authorization: Bearer <access_token>
```

## API Endpoints

### Platform Detection & Info

**POST /download/info** — Extract video metadata
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```
Response: Returns title, platform, duration, thumbnail, formats, playlist info.

**POST /download/start** — Start a direct download
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "format_id": "22",
  "as_mp3": false,
  "mp3_bitrate": "192"
}
```
Response: Returns `download_id`, file name, size, format, download URL.

**POST /download/queue** — Queue an async download
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "format_id": "22",
  "as_mp3": false,
  "mp3_bitrate": "192"
}
```
Response: Returns `task_id`, status, WebSocket URL for progress.

**GET /download/queue/{task_id}** — Poll queue status

**GET /download/file/{filename}?id={download_id}** — Serve downloaded file

**GET /download/history** — User download history (auth required)

**GET /download/recent** — Recent public downloads

**POST /download/playlist** — Extract playlist entries

**POST /download/batch** — Batch download (up to 20 URLs)

**POST /download/subtitles** — Extract subtitles

**POST /download/thumbnail** — Get video thumbnail

**GET /download/search?q={query}** — Search download history (auth required)

### Terms

**POST /download/accept-terms** — Accept Terms of Service
```json
{
  "accepted": true
}
```

### Health & Monitoring

**GET /health** — Basic health check
```json
{
  "status": "ok",
  "version": "3.1.0",
  "environment": "production",
  "database": "connected",
  "database_latency_ms": 2.3,
  "uptime_seconds": 3600.5,
  "timestamp": 1234567890.0
}
```

**GET /health/readiness** — Deep readiness check
```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "disk": "ok"
  },
  "timestamp": 1234567890.0
}
```
Returns HTTP 503 if any check fails.

**GET /metrics** — Prometheus metrics endpoint

**GET /meta** — API metadata
```json
{
  "name": "GoTot API",
  "version": "3.1.0",
  "supported_platforms": ["youtube", "tiktok", "..."],
  "documentation_url": "https://gotot.app/docs",
  "terms_url": "https://gotot.app/terms",
  "privacy_url": "https://gotot.app/privacy",
  "dmca_url": "https://gotot.app/dmca",
  "contact_email": "support@gotot.app"
}
```

## Error Responses

All errors return JSON with a `detail` field:

| Status | Meaning |
|--------|---------|
| 400 | Invalid request (bad URL, unsupported platform, malformed input) |
| 401 | Authentication required |
| 403 | Access denied (path traversal, invalid download ID) |
| 404 | File not found or expired |
| 410 | Download link expired |
| 413 | Request body too large |
| 422 | Validation error (Pydantic) |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 502 | Upstream extraction failure |
| 503 | Service not ready |

## Rate Limiting

- Global: 60 requests/minute per IP (configurable)
- Downloads: 10 requests/minute per IP (configurable)
- Returns 429 with `Retry-After` header

## Security Headers

All responses include:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Strict-Transport-Security: max-age=31536000`
- `Content-Security-Policy` (production only)
- `X-Request-ID` for request correlation
