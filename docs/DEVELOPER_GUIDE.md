# GoTot Developer Guide

Guide for developers contributing to the GoTot platform.

---

## Table of Contents

- [Environment Setup](#environment-setup)
- [Project Structure](#project-structure)
- [Backend Architecture](#backend-architecture)
- [Frontend Architecture](#frontend-architecture)
- [Adding a New Download Provider](#adding-a-new-download-provider)
- [Adding a New API Endpoint](#adding-a-new-api-endpoint)
- [Adding a New Frontend Page](#adding-a-new-frontend-page)
- [i18n System](#i18n-system)
- [Testing](#testing)
- [Code Style and Conventions](#code-style-and-conventions)
- [Database Migrations](#database-migrations)

---

## Environment Setup

### Backend

```bash
# Clone and enter the backend directory
cd backend

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
# Edit .env with your local settings

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8000
```

**Prerequisites:**
- Python 3.12+
- PostgreSQL 16 running locally
- Redis 7 running locally
- FFmpeg installed (`apt install ffmpeg` or `brew install ffmpeg`)

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local  # if available
npm run dev
```

**Prerequisites:**
- Node.js 20+
- npm (comes with Node)

### Docker (Full Stack)

```bash
docker compose up --build
```

This starts all services: nginx, frontend, backend, celery_worker, celery_beat, postgres, redis, prometheus.

---

## Project Structure

```
gotot/
├── backend/
│   ├── alembic/              # Database migrations
│   │   ├── versions/         # Migration scripts
│   │   ├── env.py            # Alembic environment config
│   │   └── script.py.mako    # Migration template
│   ├── app/
│   │   ├── main.py           # FastAPI application entry point
│   │   ├── config.py         # Pydantic settings (env-based)
│   │   ├── middleware/
│   │   │   ├── csrf.py       # CSRF protection middleware
│   │   │   ├── logging.py    # JSON request logging
│   │   │   ├── rate_limit.py # SlowAPI rate limiter
│   │   │   └── security.py   # Security headers middleware
│   │   ├── models/
│   │   │   ├── database.py   # SQLAlchemy engine, session, Base
│   │   │   ├── user.py       # User + DownloadHistory models
│   │   │   ├── download.py   # DownloadTask model
│   │   │   ├── monetization.py # Subscription, Payment, ApiKey, Referral, AffiliateLink, AdImpression
│   │   │   ├── notification.py # Notification model
│   │   │   ├── feature_flags.py # FeatureFlag model
│   │   │   └── audit.py      # AuditLog model
│   │   ├── routes/
│   │   │   ├── auth.py       # Register, login, refresh, me, profile, change password
│   │   │   ├── google_auth.py # Google OAuth login
│   │   │   ├── download.py   # Info, start, batch, playlist, queue, history, search, file serving
│   │   │   ├── payments.py   # Subscription, pay-per-download, webhooks
│   │   │   ├── api_keys.py   # Create, list, revoke
│   │   │   ├── referrals.py  # Code, apply, stats, leaderboard, history
│   │   │   ├── affiliates.py # Public affiliate links
│   │   │   ├── admin.py      # Stats, users, subs, flags, health, analytics, queue, audit, alerts
│   │   │   ├── notifications.py # List, read, mark all
│   │   │   ├── announcements.py # Active announcements
│   │   │   ├── contact.py    # Contact form
│   │   │   └── ws.py         # WebSocket progress updates
│   │   ├── services/
│   │   │   ├── auth_service.py      # JWT, bcrypt hashing
│   │   │   ├── api_key_service.py   # API key generation/validation
│   │   │   ├── downloader.py        # Video info extraction, download, MP3 conversion
│   │   │   ├── payment_service.py   # Razorpay integration, plans, webhooks
│   │   │   ├── cache.py             # Redis caching layer
│   │   │   ├── email_service.py     # SMTP email sending with templates
│   │   │   ├── notification_service.py # Database + email notifications
│   │   │   └── audit_log.py         # Structured audit logging
│   │   ├── providers/
│   │   │   ├── base.py              # Abstract BaseProvider
│   │   │   ├── registry.py          # ProviderRegistry
│   │   │   ├── youtube.py           # YouTubeProvider
│   │   │   ├── tiktok.py            # TikTokProvider
│   │   │   ├── instagram.py         # InstagramProvider
│   │   │   ├── twitter.py           # TwitterProvider
│   │   │   ├── facebook.py          # FacebookProvider
│   │   │   ├── reddit.py            # RedditProvider
│   │   │   ├── vimeo.py             # VimeoProvider
│   │   │   ├── dailymotion.py       # DailymotionProvider
│   │   │   ├── twitch.py            # TwitchProvider
│   │   │   ├── linkedin.py          # LinkedInProvider
│   │   │   ├── pinterest.py         # PinterestProvider
│   │   │   └── __init__.py          # Registry initialization
│   │   └── utils/
│   │       └── helpers.py           # URL validation, platform detection, sanitization
│   ├── celery/
│   │   ├── __init__.py      # Celery app configuration
│   │   └── tasks.py         # Download tasks, cleanup, queue status
│   ├── tests/
│   │   ├── conftest.py      # Async fixtures, mock db/user
│   │   ├── test_audit.py    # Audit logger tests
│   │   ├── test_config.py   # Settings tests
│   │   ├── test_e2e.py      # End-to-end flow tests
│   │   ├── test_helpers.py  # URL validation, platform detection
│   │   ├── test_payment.py  # Plans, limits, currency
│   │   ├── test_providers.py # Provider pattern matching
│   │   ├── test_queue.py    # Queue operations
│   │   └── test_routes.py   # API route tests
│   ├── Dockerfile
│   ├── docker-entrypoint.sh
│   ├── requirements.txt
│   ├── pyproject.toml       # Pytest configuration
│   ├── alembic.ini
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx           # Root layout with providers
│   │   │   ├── page.tsx             # Home page (download form)
│   │   │   ├── globals.css          # Tailwind + global styles
│   │   │   ├── sitemap.ts           # SEO sitemap
│   │   │   ├── download/            # Download pages (platform-specific)
│   │   │   ├── dashboard/           # User dashboard
│   │   │   ├── admin/               # Admin panel
│   │   │   ├── pricing/             # Pricing page
│   │   │   ├── login/               # Auth page
│   │   │   ├── settings/            # Account settings
│   │   │   ├── billing/             # Billing & subscription
│   │   │   ├── referrals/           # Referral program
│   │   │   ├── notifications/       # Notifications page
│   │   │   ├── blog/                # Blog page
│   │   │   ├── docs/                # Documentation
│   │   │   ├── contact/             # Contact form
│   │   │   ├── terms/               # Terms of service
│   │   │   ├── privacy/             # Privacy policy
│   │   │   ├── success/             # Payment success
│   │   │   └── offline/             # PWA offline fallback
│   │   ├── components/
│   │   │   ├── Header.tsx           # Navigation header
│   │   │   ├── Footer.tsx           # Site footer
│   │   │   ├── Hero.tsx             # Hero section
│   │   │   ├── Features.tsx         # Features grid
│   │   │   ├── DownloadForm.tsx     # URL input + submit
│   │   │   ├── ResultCard.tsx       # Format selection + download
│   │   │   ├── PlaylistViewer.tsx   # Playlist item selection
│   │   │   ├── RecentDownloads.tsx  # Public download list
│   │   │   ├── QueueProgress.tsx    # Download queue progress
│   │   │   ├── AdModal.tsx          # Optional ad/support modal
│   │   │   ├── PaymentModal.tsx     # Payment/upgrade modal
│   │   │   ├── AuthModal.tsx        # Login/register modal
│   │   │   ├── PwaRegister.tsx      # PWA install prompt
│   │   │   ├── ErrorBoundary.tsx    # React error boundary
│   │   │   ├── PageTransition.tsx   # Framer motion page transitions
│   │   │   ├── LoadingShimmer.tsx   # Skeleton loading
│   │   │   ├── NotificationBanner.tsx # Alert banners
│   │   │   ├── LocaleSwitcher.tsx   # Language selector
│   │   │   ├── AffiliateSection.tsx # Affiliate link display
│   │   │   └── Features.tsx         # Feature cards (used on multiple pages)
│   │   └── lib/
│   │       ├── api.ts              # API client (fetch wrapper)
│   │       ├── store.ts            # Zustand global state
│   │       ├── useWebSocket.ts     # WebSocket hook
│   │       └── i18n/
│   │           ├── index.ts        # Locale management
│   │           ├── en.ts           # English translations
│   │           └── es.ts           # Spanish translations
│   ├── __tests__/                   # Jest tests
│   │   ├── api.test.ts
│   │   ├── store.test.ts
│   │   └── Features.test.tsx
│   ├── Dockerfile
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── jest.config.js
│   ├── jest.setup.ts
│   └── package.json
├── nginx/
│   ├── nginx.conf
│   └── ssl/
├── scripts/
│   ├── backup.sh
│   ├── restore.sh
│   ├── init-db.sql
│   ├── generate-ssl.sh
│   └── generate-icons.py
├── docker-compose.yml
├── prometheus.yml
└── .github/workflows/ci.yml
```

---

## Backend Architecture

### Layers

```
Routes (HTTP layer)
  ↓
Services (Business logic)
  ↓
Models (Data layer / SQLAlchemy)
  ↓
Database (PostgreSQL)
```

**Middleware pipeline** (in order):
1. `JSONLogMiddleware` - Structured request/response logging
2. `SecurityHeadersMiddleware` - CSP, HSTS, XSS protection, CORS headers
3. `CSRFMiddleware` (production only) - CSRF token validation
4. `CORSMiddleware` - Cross-origin resource sharing
5. Rate limiter (SlowAPI) - Per-IP/API-key rate limiting

### Key Design Decisions

- **Async everywhere**: FastAPI + SQLAlchemy async + asyncpg + aioredis
- **Dependency injection**: `get_db()` sessions, `get_current_user()` auth
- **Provider pattern**: Each platform has a dedicated provider class inheriting from `BaseProvider`
- **Redis caching**: Video info is cached (default TTL: 1 hour) to reduce redundant fetches
- **Celery for background tasks**: Download queue, batch processing, MP3 conversion, cleanup
- **WebSocket via Redis pub/sub**: Celery tasks publish progress to Redis channels, WS endpoint subscribes

### Configuration

All settings are managed via `app/config.py` using Pydantic's `BaseSettings`. Environment variables are loaded from `.env`:

```
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql+asyncpg://gotot:gotot_pass@postgres:5432/gotot
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
ENVIRONMENT=production
RAZORPAY_KEY_ID=rzp_...
RAZORPAY_KEY_SECRET=...
SMTP_HOST=smtp.example.com
...
```

---

## Frontend Architecture

### State Management (Zustand)

Global state is managed in `store.ts` using Zustand:

```typescript
const useStore = create<DownloadState>((set) => ({
  url: "",
  videoInfo: null,
  downloadResult: null,
  isLoading: false,
  error: null,
  user: null,
  subscription: null,
  isDarkMode: false,
  // ... more state
}));
```

### API Client (`lib/api.ts`)

A fetch-based wrapper that:
- Automatically attaches `Authorization` headers
- Handles JWT refresh on 401 responses
- Provides typed interface methods for every endpoint
- Stores tokens in `localStorage`

### Pages & Routing (Next.js App Router)

```
/                    → Home (download form)
/download/{platform} → Platform-specific download pages
/dashboard           → User dashboard
/dashboard/history   → Download history
/dashboard/api-keys  → API key management
/dashboard/billing   → Subscription & payment
/dashboard/referrals → Referral program
/dashboard/settings  → Account settings
/admin               → Admin panel
/pricing             → Pricing plans
/login               → Auth (login/register)
/notifications       → Notification center
/contact             → Contact form
/terms               → Terms of service
/privacy             → Privacy policy
/blog                → Blog
/docs                → Documentation
/success             → Payment success page
/offline             → PWA offline fallback
```

### Components

- **DownloadForm** — URL input with platform auto-detection
- **ResultCard** — Download results with format selection, quality tabs, MP3 bitrate, sharing
- **PlaylistViewer** — Playlist item selection with checkboxes
- **QueueProgress** — Real-time download progress (via WebSocket)
- **PaymentModal** — Upgrade/pay-per-download prompts
- **AdModal** — Optional "support us" modal (no forced ads)
- **PwaRegister** — PWA install prompt component

---

## Adding a New Download Provider

1. **Create the provider file** at `backend/app/providers/{name}.py`

```python
import re
from typing import Optional
from app.providers.base import BaseProvider

class MyPlatformProvider(BaseProvider):
    name = "myplatform"
    display_name = "My Platform"
    color = "#FF0000"
    patterns = [
        r"^https?://(?:www\.)?myplatform\.com/(?:watch|video)/([\w-]+)",
        r"^https?://(?:www\.)?myplatform\.com/\w+/\w+",
    ]

    def extract_info(self, url: str, ydl_opts: Optional[dict] = None) -> Optional[dict]:
        # Use yt-dlp to extract video information
        import yt_dlp
        opts = ydl_opts or {"quiet": True, "no_warnings": True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                return ydl.extract_info(url, download=False)
            except Exception:
                return None

    def extract_playlist(self, url: str, ydl_opts: Optional[dict] = None) -> Optional[list]:
        # Return list of entries or None
        ...
```

2. **Register the provider** in `backend/app/providers/__init__.py`:

```python
from app.providers.myplatform import MyPlatformProvider

def register_all_providers():
    registry = ProviderRegistry()
    for provider_cls in [
        YouTubeProvider,
        TikTokProvider,
        # ... existing providers ...
        MyPlatformProvider,  # <-- add here
    ]:
        registry.register(provider_cls())
    return registry
```

3. **Add URL patterns** to the platform detection helper in `backend/app/services/downloader.py` if needed (usually automatic via provider patterns).

4. **Add i18n translations** in `frontend/src/lib/i18n/en.ts` and `es.ts` for the platform name.

5. **Add a download page** at `frontend/src/app/download/{name}/page.tsx`.

6. **Update the sitemap** at `frontend/src/app/sitemap.ts`.

7. **Add tests** in `backend/tests/test_providers.py`.

---

## Adding a New API Endpoint

### Backend

1. **Create the route** in `backend/app/routes/{name}.py`:

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/my-feature", tags=["my-feature"])

class MyRequest(BaseModel):
    field: str

@router.post("/action")
async def my_action(data: MyRequest):
    return {"result": "success"}
```

2. **Register the router** in `backend/app/main.py`:

```python
from app.routes import my_feature
app.include_router(my_feature.router)
```

3. **Add business logic** in `backend/app/services/{name}_service.py`.

4. **Add a model** in `backend/app/models/{name}.py` if persistent storage is needed.

5. **Create a database migration**:
```bash
cd backend
alembic revision --autogenerate -m "add my_feature table"
alembic upgrade head
```

6. **Add tests** in `backend/tests/`.

### Frontend

1. **Add API method** in `frontend/src/lib/api.ts`:

```typescript
myAction: (field: string) =>
  request<{ result: string }>("/my-feature/action", {
    method: "POST",
    body: { field },
  }),
```

2. **Add state** in `frontend/src/lib/store.ts` if needed.

3. **Create a page** or **component** that calls the new API.

---

## Adding a New Frontend Page

1. **Create the page** at `frontend/src/app/{path}/page.tsx`:

```tsx
"use client";
import { motion } from "framer-motion";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

export default function MyPage() {
  return (
    <>
      <Header />
      <motion.main initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <h1>My New Page</h1>
      </motion.main>
      <Footer />
    </>
  );
}
```

2. **Add translations** for any new copy in `frontend/src/lib/i18n/en.ts` and `es.ts`.

3. **Wire up API calls** using `api.ts` methods.

4. **Add state** to `store.ts` if the page needs global state.

5. **Add the route** to navigation in `Header.tsx` if it's a top-level page.

---

## i18n System

GoTot uses a simple dictionary-based i18n system (no framework dependency).

### Adding a New Language

1. **Create the translation file** at `frontend/src/lib/i18n/{lang}.ts`:

```typescript
import { en } from "./en";

export const fr: typeof en = {
  nav: {
    home: "Accueil",
    pricing: "Tarifs",
    // ... translate all keys
  },
  // ...
};
```

2. **Register the locale** in `frontend/src/lib/i18n/index.ts`:

```typescript
import { fr } from "./fr";

export type Locale = "en" | "es" | "fr";

const translations: Record<Locale, TranslationDict> = { en, es, fr };
```

3. **Add the locale to the switcher** in `LocaleSwitcher.tsx`.

### Usage in Components

```tsx
import { useLocale } from "@/lib/i18n";

function MyComponent() {
  const { locale, t } = useLocale();
  return <h1>{t.hero.title}</h1>;
}
```

---

## Testing

### Backend (pytest)

```bash
# Run all tests
cd backend
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_helpers.py -v

# Run tests matching pattern
pytest -k "provider"
```

Configuration is in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --tb=short"
```

### Frontend (Jest)

```bash
# Run all tests
cd frontend
npm test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage
```

Configuration is in `jest.config.js` with TypeScript support via `ts-jest`.

### Writing Tests

**Backend (async):**
```python
import pytest

@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in ("ok", "degraded")
```

**Frontend:**
```typescript
import { render, screen } from "@testing-library/react";
import Features from "@/components/Features";

test("renders all feature cards", () => {
  render(<Features />);
  expect(screen.getByText("11+ Platforms")).toBeInTheDocument();
});
```

---

## Code Style and Conventions

### Python

- **Python 3.12+**: Use modern syntax (`str | None` over `Optional[str]`)
- **Type hints**: Required for all function signatures
- **Line length**: 120 characters
- **Imports**: Standard library → third-party → local (alphabetical within groups)
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants
- **Async/await**: Use `async def` for route handlers, `await` for DB/IO calls
- **Error handling**: Raise `HTTPException` with appropriate status codes in routes

### TypeScript

- **TypeScript 5.5+**: Strict mode enabled
- **Type definitions**: Create interfaces for API responses and component props
- **Naming**: `camelCase` for functions/variables, `PascalCase` for components and interfaces
- **React**: Functional components with hooks, no class components
- **Client components**: Use `"use client"` directive for interactive components
- **Imports**: Use `@/` path alias for `src/` directory

### SQLAlchemy

- **Async sessions**: Use `async with async_session() as session`
- **Models**: Use `Mapped[]` type annotations with `mapped_column()`
- **UUID primary keys**: Use `UUID(as_uuid=True)` with `default=uuid.uuid4`
- **Timestamps**: Use `DateTime` with `default=datetime.utcnow`
- **Enums**: Use Python `enum.Enum` with SQLAlchemy's `SAEnum`

### Git

- **Branch naming**: `feature/description`, `fix/description`, `chore/description`
- **Commit messages**: Concise, imperative mood, 72 char title
- **CI**: Tests, linting, and build must pass before merging to `main`

---

## Database Migrations

GoTot uses **Alembic** with async support for database migrations.

### Initial Setup

```bash
cd backend

# Initialize (already done)
alembic init alembic

# Create a new migration
alembic revision --autogenerate -m "add user table"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1

# View history
alembic history

# View current revision
alembic current
```

### Migration Configuration (`alembic/env.py`)

- Uses `run_async()` for async engine context
- Auto-detects model changes from `Base.metadata`
- Reads `DATABASE_URL` from settings/config

### Best Practices

- Always review auto-generated migrations before committing
- Test migrations on a copy of production data
- Never edit existing migration files — create a new one
- Use `batch` operations for large table alterations
- Include both `upgrade()` and `downgrade()` functions

### Creating Migrations

```bash
# After modifying models, run:
alembic revision --autogenerate -m "describe your change"

# Check the generated file in alembic/versions/
# Then apply:
alembic upgrade head
```
