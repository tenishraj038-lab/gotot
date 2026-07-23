# GoTot — Universal Multi-Platform Video Downloader

Download videos from 15+ platforms — TikTok, Instagram, X/Twitter, Facebook, Reddit, Vimeo, Dailymotion, Twitch, LinkedIn, Pinterest, Snapchat, Bilibili, SoundCloud, Rumble, and Odysee. Free, fast, secure.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Cloudflare     │────▶│  Render (free)  │────▶│  Supabase (free) │
│  Pages (front)  │     │  FastAPI (back) │     │  PostgreSQL      │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │  Upstash (free)  │
                        │  Redis           │
                        └─────────────────┘
```

## Tech Stack

| Layer | Technology | Free Tier |
|-------|-----------|-----------|
| Frontend | Next.js 14 + Tailwind | Cloudflare Pages |
| Backend | FastAPI (Python 3.12) | Render |
| Database | PostgreSQL | Supabase (500MB) |
| Cache | Redis | Upstash (10K cmds/day) |
| Media | yt-dlp + FFmpeg | Render disk (ephemeral) |
| Monitoring | Prometheus + Grafana | Self-hosted (optional) |

## Quick Start (Local Development)

```bash
# Terminal 1 — Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit with your values
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

## Production Deployment (Free Tier)

See [DEPLOY.md](DEPLOY.md) for step-by-step instructions. Deploys in ~15 minutes.

## Environment Variables

| Variable | Backend | Frontend |
|----------|---------|----------|
| `SECRET_KEY` | Required (64 chars) | — |
| `DATABASE_URL` | Supabase connection | — |
| `REDIS_URL` | Upstash connection | — |
| `ALLOWED_ORIGINS` | Frontend URL | — |
| `FRONTEND_URL` | Frontend URL | — |
| `RAZORPAY_KEY_ID` | Optional | — |
| `SENTRY_DSN` | Optional | — |
| `NEXT_PUBLIC_API_URL` | — | `/api` |

## Security

- Rate limiting (100 req/min)
- CSRF protection (production)
- HSTS, CSP, X-Frame-Options headers
- SSRF protection (blocked schemes + private IPs)
- Cookie consent (GA gated)
- .env gitignored — secrets never committed

## Supported Platforms

TikTok, Instagram, Twitter/X, Facebook, Reddit, Vimeo, Dailymotion, Twitch, LinkedIn, Pinterest, Snapchat, Bilibili, SoundCloud, Rumble, Odysee.

GoTot is independent and not affiliated with any listed platform. All trademarks belong to their respective owners.

## Legal

- [Terms of Service](https://gotot.app/terms)
- [Privacy Policy](https://gotot.app/privacy)
- [Copyright Policy](https://gotot.app/copyright)
- [DMCA Policy](https://gotot.app/dmca)

## License

All rights reserved. See LICENSE.
