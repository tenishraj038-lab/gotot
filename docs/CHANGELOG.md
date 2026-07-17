# Changelog

All notable changes to GoTot are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and GoTot follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.0.0] - 2026-03-15

### Added

#### New Platforms
- **YouTube** — Full support including shorts, playlists, and 4K downloads
- **TikTok** — Video downloads without watermark
- **Instagram** — Posts, reels, and story downloads
- **Twitter/X** — Video and GIF downloads from tweets
- **Facebook** — Public video downloads
- **Reddit** — Video downloads from posts
- **Vimeo** — High-quality video downloads
- **Twitch** — Clip and VOD downloads
- **Dailymotion** — Video downloads
- **LinkedIn** — Event and feed video downloads
- **Pinterest** — Video pin downloads

#### Authentication
- Email/password registration and login
- Google OAuth sign-in with auto-provisioning
- JWT access tokens (60 min) with refresh token rotation (30 day)
- Refresh token versioning for session invalidation
- Password change with session rotation

#### Download System
- Video info extraction with format discovery
- Format selection with quality labels (360p to 4K)
- MP3 audio extraction with bitrate selection (128-320 kbps)
- Batch download (up to 20 URLs)
- Playlist detection and extraction
- Asynchronous download queue via Celery
- Real-time download progress via WebSocket
- File serving with path traversal protection
- Download history for authenticated users
- Download search by URL

#### Subscription & Payments
- Three-tier plan system: Free, Pro ($4.99/mo), Unlimited ($9.99/mo)
- Razorpay integration for recurring subscriptions
- Razorpay payment links for pay-per-download ($0.50 per download)
- Webhook handling for payment events (captured, subscription charged/cancelled)
- HMAC-SHA256 webhook signature verification
- Automatic subscription activation and cancellation
- Payment history for users
- Pay-per-download credit system (2 credits per purchase)

#### API Keys
- API key generation with SHA-256 hashed storage
- Rate limits by tier (50/1K/10K requests per day)
- Key creation, listing, and revocation
- Header-based authentication (`X-API-Key`)

#### Referral Program
- Unique referral code generation (`GOTOT` prefix + 6 chars)
- +3 bonus downloads per successful referral
- Referral stats (total, weekly, monthly, pending)
- Referral leaderboard with badges (gold, silver, bronze, top10/50/100)
- Referral history with status tracking

#### Admin Panel
- Dashboard statistics (users, downloads, revenue, subscriptions)
- User management (list, search, ban/unban, delete)
- Subscription management (list, cancel)
- Feature flag system (create, toggle)
- System health monitoring (database, Redis, config)
- Download analytics (by platform, format, daily trends)
- Affiliate link management (CRUD)
- Download queue monitoring (pending, processing, completed, failed)
- Audit log search and filtering
- System alerts (failed downloads, payments, user growth)

#### Notifications
- In-app notification system with read/unread tracking
- 10 notification types (download complete/failed, payment, referral, security, etc.)
- Unread count endpoint
- Mark single/all as read

#### Contact System
- Contact form submission with validation
- Email notification to admin on new submissions

#### Announcements
- Active announcement endpoint for platform-wide messages

#### Affiliate Links
- Public affiliate link listing
- Click tracking with counter

#### Infrastructure
- Docker Compose deployment with 9 services (nginx, frontend, backend, celery_worker, celery_beat, postgres, redis, prometheus, backup)
- Automated database backups every 6 hours with 30-day retention
- Backup integrity verification (gzip test)
- Database restore script with confirmation prompt
- Let's Encrypt SSL support
- Self-signed SSL generation script
- Prometheus metrics at `/metrics`
- Prometheus scrape configuration for backend and nginx
- GitHub Actions CI/CD pipeline (backend tests, frontend checks, Docker build)
- Celery beat for scheduled cleanup tasks
- Alembic database migrations with async support

#### Frontend
- Next.js 14 App Router with SSR and client components
- Zustand global state management
- Tailwind CSS with dark mode support
- Framer Motion page transitions and animations
- PWA support with service worker and install prompt
- i18n system with English and Spanish translations
- Platform auto-detection on URL paste
- Responsive layout for all device sizes
- SEO optimization with JSON-LD structured data (FAQ, HowTo, WebApplication)
- Sitemap generation for all 11 platform pages
- Canonical URLs and OpenGraph metadata
- Social sharing buttons (WhatsApp, Twitter, Facebook, Copy)
- Playlist viewer with multi-select checkboxes
- Recent downloads feed (privacy-safe, no URLs exposed)
- Payment modal and upgrade prompts
- Optional ad/support modal (no forced ads)
- Error boundary for graceful failure handling

#### Email System
- SMTP-based email sending (SendGrid compatible)
- HTML email templates with responsive design
- Welcome email on registration
- Email verification flow
- Password reset flow
- Premium purchase confirmation
- Subscription renewal notifications
- Referral reward notifications
- Weekly summary emails
- Security alert emails
- Contact form notification to admin
- User email preference controls (security_alerts, product_updates, marketing)

#### Security
- CSRF protection via double-submit cookie pattern (production only)
- Security headers (CSP, HSTS, XSS Protection, Frame Options, etc.)
- CORS middleware with configurable origins
- Rate limiting via SlowAPI with Redis backend
- SQL injection prevention via parameterized queries
- Path traversal protection for file downloads
- bcrypt password hashing with 12 salt rounds
- JWT with refresh token rotation
- API key hashing with SHA-256
- Sentry error tracking
- Structured JSON logging for all HTTP requests
- Global exception handler (no stack trace leakage)

#### Caching
- Redis-based video info caching (1 hour TTL)
- Graceful degradation when Redis is unavailable
- Cache-aside pattern (lazy population)

#### WebSocket
- Real-time download progress via WebSocket
- Redis pub/sub for Celery task → WebSocket bridge
- Connection manager with per-task channels
- Multi-client support per task

### Changed

#### From v2.x
- Complete backend rewrite from Flask to FastAPI with async support
- Database migration from SQLite to PostgreSQL 16
- Frontend migration from Create React App to Next.js 14 App Router
- Payment provider switched to Razorpay
- Authentication migrated to JWT with refresh token rotation
- Download system rewritten with provider pattern for multi-platform support
- Queue system migrated from Redis RQ to Celery
- Caching layer added with Redis
- Monitoring added with Prometheus
- Backup system automated with Docker cron service

### Fixed

- Privacy leak in recent downloads (no longer exposes user URLs)
- Anonymous user download limits removed (unlimited free downloads)
- MP3 extraction made free for all tiers
- Batch download limit increased to 20 URLs
- Platform URL pattern detection expanded (short URLs, embeds, clips, reels, shorts)
- Playlist URL extraction now uses correct entry URL
- Format deduplication improved with quality-aware sorting
- Missing `title` and `thumbnail_url` in download history records
- Video info caching race condition fixed with atomic setex

### Security

- Refresh token rotation implemented to prevent token replay attacks
- CSRF protection added for production environment
- Path traversal protection added to file serving endpoint
- SQL wildcard characters sanitized in search queries
- API keys stored as SHA-256 hashes (never plaintext)
- Non-root users in all Docker containers
- Sentry error tracking configured
- Security headers hardened (CSP, HSTS, XSS, Frame Options, etc.)

---

## [2.0.0] - 2025-12-01

### Added
- Initial multi-platform download support (YouTube, TikTok, Instagram)
- Basic user authentication system
- Download queue with Redis RQ
- Simple admin dashboard
- Payment integration with Razorpay
- Frontend with Create React App

---

## [1.0.0] - 2025-06-15

### Added
- Initial release with YouTube-only downloads
- Flask backend with SQLite
- Basic HTML/CSS frontend
- Manual download processing
