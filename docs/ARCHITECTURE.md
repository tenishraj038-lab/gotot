# GoTot System Architecture

Comprehensive overview of the GoTot platform architecture, data flows, and design decisions.

---

## Table of Contents

- [High-Level Architecture](#high-level-architecture)
- [Component Overview](#component-overview)
- [Data Flow: Download Request Lifecycle](#data-flow-download-request-lifecycle)
- [Authentication Flow](#authentication-flow)
- [Payment Flow](#payment-flow)
- [Queue Processing](#queue-processing)
- [WebSocket Real-Time Updates](#websocket-real-time-updates)
- [Caching Strategy](#caching-strategy)
- [Security Architecture](#security-architecture)

---

## High-Level Architecture

```
                          ┌─────────────────────────────────────────────────────────┐
                          │                      Internet                           │
                          └────────────────────────┬────────────────────────────────┘
                                                   │
                                              ┌────┴────┐
                                              │  Nginx   │  Reverse Proxy / SSL Termination
                                              │ :443/80  │
                                              └────┬────┘
                                                   │
                          ┌────────────────────────┼────────────────────────┐
                          │                        │                        │
                          ▼                        ▼                        ▼
                   ┌───────────┐          ┌──────────────┐         ┌──────────────┐
                   │  Frontend │  /api/*  │   Backend    │  /ws/*  │  WebSocket   │
                   │  Next.js  │◄────────►│   FastAPI    │◄───────►│  /ws/progress│
                   │  :3000    │  rewrite │   :8000      │         │  │
                   └─────┬─────┘          └──────┬───────┘         └──────┬──────┘
                         │                       │                        │
                         │                       │                        │
                         │              ┌────────┴────────┐               │
                         │              │   PostgreSQL    │               │
                         │              │    :5432        │               │
                         │              └────────┬────────┘               │
                         │                       │                        │
                         │              ┌────────┴────────┐               │
                         │              │     Redis       │◄──────────────┘
                         │              │    :6379        │  Pub/Sub progress
                         │              └────────┬────────┘
                         │                       │
                         │              ┌────────┴────────┐
                         │              │     Celery      │
                         │              │  Worker / Beat  │
                         │              └─────────────────┘
                         │
                   ┌─────┴─────┐
                   │  Prometheus│
                   │  :9090    │
                   └───────────┘
```

---

## Component Overview

### Nginx

- **Role**: Reverse proxy, SSL termination, static file serving
- **Ports**: 80 (HTTP → HTTPS redirect), 443 (HTTPS)
- **Load balancing**: Least-connections across upstream services
- **WebSocket support**: Protocol upgrade for WS connections
- **Security headers**: HSTS, XSS protection, CSP, CORS via backend
- **Rate limiting**: N/A (handled at backend layer)

### Frontend (Next.js 14)

- **Framework**: Next.js 14 with App Router
- **Rendering**: Server-side rendering (SSR) + client-side components
- **State**: Zustand for global state
- **Styling**: Tailwind CSS with dark mode support
- **Animations**: Framer Motion
- **API Client**: Custom fetch-based client with automatic JWT refresh
- **i18n**: Dictionary-based (English, Spanish)
- **PWA**: Service worker for offline support and installability

### Backend (FastAPI)

- **Framework**: FastAPI with async support
- **ORM**: SQLAlchemy 2.0 async with asyncpg driver
- **Auth**: JWT (python-jose) + bcrypt (passlib) + refresh token rotation
- **Rate limiting**: SlowAPI with Redis backend
- **Validation**: Pydantic v2 for request/response models
- **Background tasks**: Celery with Redis broker
- **Caching**: Redis cache layer (video info, 1h TTL)
- **Monitoring**: Prometheus metrics at `/metrics`
- **Error tracking**: Sentry SDK

### PostgreSQL 16

- **Role**: Primary data store
- **Connection pool**: 20 pool size, 10 overflow
- **Migration**: Alembic with async support
- **Extensions**: uuid-ossp, pgcrypto

### Redis 7

- **Role**: Cache, Celery broker, Celery result backend, Pub/Sub for WebSockets
- **Memory**: 512 MB max, allkeys-lru eviction
- **Persistence**: Append-only file
- **Databases**: 0 (cache/pubsub), 1 (Celery broker)

### Celery

- **Broker**: Redis (db 1)
- **Result backend**: Redis (db 0)
- **Worker concurrency**: 4 (configurable)
- **Key tasks**:
  - `process_download` — Download a single video (queue: `downloads`)
  - `process_batch_download` — Download multiple videos (queue: `downloads`)
  - `process_mp3_conversion` — Convert video to MP3 (queue: `conversions`)
  - `cleanup_temp_files` — Remove expired temp files (beat: hourly)
- **Task time limit**: 30 minutes (hard), 25 minutes (soft)
- **Max tasks per child**: 200 (memory management)

### Prometheus

- **Scrape interval**: 15s
- **Targets**: Backend (`:8000`), Nginx (`:80`)
- **Storage**: Local volume with retention defaults

---

## Data Flow: Download Request Lifecycle

### Sync Download (Direct)

```
User ──→ Frontend ──POST /download/info──→ Backend
                                             │
                                    ┌────────┴────────┐
                                    │  Check Redis    │
                                    │  Cache          │
                                    └────────┬────────┘
                                             │ Cache miss?
                                    ┌────────┴────────┐
                                    │  Detect Platform│
                                    │  (Provider)     │
                                    └────────┬────────┘
                                             │
                                    ┌────────┴────────┐
                                    │  yt-dlp extract │
                                    │  info           │
                                    └────────┬────────┘
                                             │
                                    ┌────────┴────────┐
                                    │  Store in Redis │
                                    │  Cache (3600s)  │
                                    └────────┬────────┘
                                             │
User ◄── Frontend ◄── Formats list ◄─────────┘

User selects format
        │
        ▼
Frontend ──POST /download/start──→ Backend
                                      │
                             ┌────────┴────────┐
                             │  Check limits   │
                             │  (daily, credits)│
                             └────────┬────────┘
                                      │
                             ┌────────┴────────┐
                             │  yt-dlp download│
                             │  → /tmp/downloads│
                             └────────┬────────┘
                                      │
                             ┌────────┴────────┐
                             │  Save Download  │
                             │  History (DB)   │
                             └────────┬────────┘
                                      │
User ◄── Frontend ◄── Download URL ◄──┘
        │
        ▼
User clicks download URL
        │
        ▼
Frontend ──GET /download/file/{name}──→ Backend
                                          │
                                 ┌────────┴────────┐
                                 │  Path traversal │
                                 │  check          │
                                 └────────┬────────┘
                                          │
User ◄── Backend serves file ◄────────────┘
        (FileResponse with Content-Disposition)
```

### Async Download (Queued)

```
User ──POST /download/queue──→ Backend
                                  │
                         ┌────────┴────────┐
                         │  Generate task_id│
                         │  Save record    │
                         └────────┬────────┘
                                  │
                          celery_task.delay()
                                  │
User ◄── { task_id, ws_url } ◄────┘
        │
        ▼
Frontend connects to WebSocket /ws/progress/{task_id}
        │
        ▼
Celery Worker picks up task
        │
        ├──→ Pub to Redis: progress:{task_id} (queued)
        ├──→ Pub to Redis: progress:{task_id} (downloading 10%)
        ├──→ Pub to Redis: progress:{task_id} (processing 80%)
        └──→ Pub to Redis: progress:{task_id} (completed 100%)
                │
                ▼
        WS Connection Manager (Redis Sub)
                │
                ▼
        WebSocket sends JSON to client
                │
                ▼
        Frontend updates QueueProgress component
```

---

## Authentication Flow

### Registration

```
User ──POST /auth/register──→ Backend
                                 │
                        ┌───────┴────────┐
                        │  Validate input │
                        │  (email, pwd)   │
                        └───────┬────────┘
                                │
                        ┌───────┴────────┐
                        │  Check existing │
                        │  409 if dup     │
                        └───────┬────────┘
                                │
                        ┌───────┴────────┐
                        │  Hash pwd      │
                        │  (bcrypt)       │
                        └───────┬────────┘
                                │
                        ┌───────┴────────┐
                        │  Create User   │
                        │  Save to DB    │
                        └───────┬────────┘
                                │
                        ┌───────┴────────┐
                        │  Issue tokens  │
                        │  access (60m)  │
                        │  refresh (30d) │
                        └───────┬────────┘
                                │
User ◄── { access, refresh } ◄─┘
```

### Login

```
User ──POST /auth/login──→ Backend
                              │
                     ┌───────┴────────┐
                     │  Find by email │
                     │  Verify pwd    │
                     └───────┬────────┘
                             │ fail → 401
                     ┌───────┴────────┐
                     │  Check is_active│
                     └───────┬────────┘
                             │ inactive → 403
                     ┌───────┴────────┐
                     │  Issue tokens  │
                     └───────┬────────┘
                             │
User ◄── { access, refresh } ─┘
```

### Token Refresh

```
Client ──POST /auth/refresh──→ Backend
                                  │
                         ┌────────┴────────┐
                         │  Decode refresh  │
                         │  token           │
                         └────────┬────────┘
                                  │ invalid → 401
                         ┌────────┴────────┐
                         │  Check token    │
                         │  version (ver)  │
                         │  vs DB version  │
                         └────────┬────────┘
                                  │ mismatch → 401 (revoked)
                         ┌────────┴────────┐
                         │  Increment DB   │
                         │  version (invalidate)│
                         └────────┬────────┘
                                  │
                         ┌────────┴────────┐
                         │  Issue NEW pair │
                         └────────┬────────┘
                                  │
Client ◄── { new access, new refresh } ─┘
```

### Google OAuth

```
User ──→ Frontend (Google Sign-In button)
        │
        ├──→ Google OAuth popup
        │   └──→ Google returns ID token
        │
        ▼
Frontend ──POST /auth/google/login { id_token }──→ Backend
                                                      │
                                             ┌────────┴────────┐
                                             │  Verify with    │
                                             │  Google API     │
                                             └────────┬────────┘
                                                      │ fail → 401
                                             ┌────────┴────────┐
                                             │  Check aud     │
                                             │  matches client │
                                             └────────┬────────┘
                                                      │
                                             ┌────────┴────────┐
                                             │  Find or create  │
                                             │  user by email   │
                                             └────────┬────────┘
                                                      │
                                             ┌────────┴────────┐
                                             │  Issue tokens   │
                                             └────────┬────────┘
                                                      │
User ◄── { access, refresh, is_new } ◄────────────────┘
```

---

## Payment Flow

### Subscription Purchase

```
User ──POST /payment/create-subscription { tier }──→ Backend
                                                        │
                                               ┌────────┴────────┐
                                               │  Get plan from  │
                                               │  PLANS dict     │
                                               └────────┬────────┘
                                                        │
                                               ┌────────┴────────┐
                                               │  Create Razorpay│
                                               │  subscription   │
                                               └────────┬────────┘
                                                        │
User ◄── { checkout_url } ◄─────────────────────────────┘
        │
        ▼
User completes payment on Razorpay checkout page
        │
        ▼
Razorpay ──POST /payment/webhook (subscription.charged)──→ Backend
                                                              │
                                                     ┌────────┴────────┐
                                                     │  Verify HMAC    │
                                                     │  signature      │
                                                     └────────┬────────┘
                                                              │ fail → 400
                                                     ┌────────┴────────┐
                                                     │  Find or create │
                                                     │  Subscription   │
                                                     └────────┬────────┘
                                                              │
                                                     ┌────────┴────────┐
                                                     │  Update user    │
                                                     │  role to tier   │
                                                     └────────┬────────┘
                                                              │
User ◄── (next page load shows upgraded status) ◄──────────────┘
```

### Pay-Per-Download

```
User ──POST /payment/pay-per-download──→ Backend
                                            │
                                   ┌────────┴────────┐
                                   │  Create Razorpay│
                                   │  payment link   │
                                   │  (50¢ USD)      │
                                   └────────┬────────┘
                                            │
User ◄── { checkout_url } ◄─────────────────┘
        │
        ▼
User completes payment
        │
        ▼
Razorpay ──POST /payment/webhook (payment.captured)──→ Backend
                                                          │
                                                 ┌────────┴────────┐
                                                 │  Verify HMAC    │
                                                 └────────┬────────┘
                                                          │
                                                 ┌────────┴────────┐
                                                 │  Add 2 download │
                                                 │  credits to user│
                                                 └────────┬────────┘
                                                          │
User ◄── credits updated ◄─────────────────────────────────┘
```

---

## Queue Processing

### Architecture

```
HTTP Request ──→ Backend ──→ Celery Task (delay)
                                    │
                                    ▼
                          ┌─────────────────┐
                          │  Redis Broker    │
                          │  (db 1)         │
                          └────────┬────────┘
                                   │
                          ┌────────┴────────┐
                          │  Celery Worker  │
                          │  (concurrency:4)│
                          └────────┬────────┘
                                   │
                          ┌────────┴────────┐
                          │  yt-dlp download│
                          │  → /tmp/downloads│
                          └────────┬────────┘
                                   │
                          ┌────────┴────────┐
                          │  Redis Pub/Sub  │
                          │  progress:uuid  │
                          └────────┬────────┘
                                   │
                          ┌────────┴────────┐
                          │  WS Connection  │
                          │  Manager        │
                          └────────┬────────┘
                                   │
                          Client WebSocket
```

### Task States

```
queued ──→ downloading ──→ processing ──→ completed
              │                                │
              └──→ error ◄─────────────────────┘
```

### Scheduled Tasks (Celery Beat)

| Task | Schedule | Description |
|------|----------|-------------|
| `cleanup_temp_files` | Every hour | Remove files in `/tmp/downloads` older than 1 hour |

---

## WebSocket Real-Time Updates

### Connection Flow

```
1. Client posts /download/queue
2. Server returns task_id + ws_url
3. Client opens WebSocket to /ws/progress/{task_id}
4. Server accepts and subscribes to Redis channel progress:{task_id}
5. Celery worker publishes progress updates via Redis pub/sub
6. WS Connection Manager forwards updates to connected clients
7. Client disconnects (closes tab or task completes)
8. Worker's final update is the last message
```

### Connection Manager Architecture

```python
class ConnectionManager:
    active: Dict[str, Set[WebSocket]]
    # task_id → set of connected websockets

    pubsub_connections: Dict[str, asyncio.Task]
    # task_id → asyncio task for Redis listener
```

- Each task_id gets exactly one Redis pub/sub listener
- Multiple WebSocket clients can connect to the same task_id
- When all clients disconnect, the Redis listener is cleaned up

---

## Caching Strategy

### Redis Cache Layers

| Cache Key Prefix | TTL | Description |
|-----------------|-----|-------------|
| `vinfo:{url}` | 3600s (1h) | Video info results |
| `progress:{task_id}` | N/A (pub/sub) | Real-time download progress |

### Cache Invalidation

- Video info cache: TTL-based expiry (1 hour)
- No explicit invalidation (video info is immutable per URL)
- Cache is skipped if Redis is unavailable (graceful degradation)

### Cache Flow

```
Request for video info
        │
        ▼
┌─── Check Redis ───┐
│  Key: vinfo:{url}  │─── Hit ──→ Return cached data
└────────┬───────────┘
         │ Miss
         ▼
Extract via yt-dlp
         │
         ▼
Store in Redis
(3600s TTL)
         │
         ▼
Return to client
```

### Graceful Degradation

All caching is optional. If Redis is unavailable:
- `cache_get()` returns `None`
- `cache_set()` logs a debug message and continues
- The application works without caching (slightly slower)

---

## Security Architecture

### Layered Security

```
Layer 1: Nginx
├── HTTPS (TLS 1.2/1.3)
├── HSTS, CSP, XSS headers
├── Rate limiting (TCP level)
└── Block .git, .env paths

Layer 2: Backend Middleware
├── JSONLogMiddleware (request logging)
├── SecurityHeadersMiddleware (CSP, HSTS, etc.)
├── CSRFMiddleware (production only)
├── CORSMiddleware (configurable origins)
└── Rate Limiter (SlowAPI, per-IP/key)

Layer 3: Application
├── JWT auth (Bearer token)
├── API key auth (X-API-Key header)
├── Pydantic validation (input sanitization)
├── Password hashing (bcrypt)
└── Path traversal protection (file serving)

Layer 4: Database
├── Parameterized queries (SQLAlchemy)
├── Connection validation (pool_pre_ping)
└── Least privilege user
```

### Security Headers (Set by Backend)

| Header | Value |
|--------|-------|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `X-XSS-Protection` | `1; mode=block` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` |
| `Content-Security-Policy` | (production only, configurable) |

### CSRF Protection

- Only active in production
- Exempts: `/health`, `/contact`, `/auth/register`, `/auth/login`, `/auth/refresh`
- Exempts authenticated requests (Bearer tokens and API keys)
- Uses double-submit cookie pattern (cookie + header)

### API Key Security

- Keys prefixed with `gt_` for identifiability
- Stored as SHA-256 hash (never plaintext)
- Shown only once at creation
- Rate-limited per key per day
- Revocable by user or admin
