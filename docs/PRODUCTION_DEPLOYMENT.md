# GoToT Production Deployment Guide

## Architecture

```
User → Vercel (Frontend) → Rewrites /api/* → Render (Backend API)
                                           → Direct WS → Render (WebSocket)
                                              ↓
                                    Supabase (PostgreSQL)
                                    Upstash (Redis)
                                    Cloudinary (optional - video storage)
                                    Razorpay (Payments)
                                    Sentry (Error Tracking)
```

- **Frontend**: Next.js 14 (App Router) on Vercel (free tier)
- **Backend**: FastAPI on Render Web Service (free tier)
- **Database**: Supabase PostgreSQL (free tier - 500MB)
- **Redis**: Upstash Redis (free tier - 30MB)
- **Payments**: Razorpay
- **Auth**: JWT + Google OAuth
- **Monitoring**: Sentry (free) + UptimeRobot (free) + Google Analytics (free)

---

## Prerequisites

Sign up for these free accounts:

| Service | Tier | Link |
|---------|------|------|
| GitHub | Free | https://github.com |
| Vercel | Free (Hobby) | https://vercel.com |
| Render | Free | https://render.com |
| Supabase | Free | https://supabase.com |
| Upstash | Free | https://upstash.com |
| Sentry | Free | https://sentry.io |
| Razorpay | Live/Sandbox | https://razorpay.com |
| UptimeRobot | Free | https://uptimerobot.com |
| Google Analytics | Free | https://analytics.google.com |

---

## Step 1 – Supabase (PostgreSQL)

1. Go to https://supabase.com and sign up
2. Create a new project (choose a strong database password, save it)
3. Wait for the database to provision (~2 min)
4. Go to **Project Settings → Database → Connection string**
5. Copy the URI: `postgresql://postgres:YOUR_PASSWORD@db.YOUR_REF.supabase.co:5432/postgres`
6. Note: Replace `YOUR_PASSWORD` and `YOUR_REF` with actual values
7. Go to **SQL Editor** and run the migration from `backend/alembic/versions/001_initial_schema.py` or let Render run `alembic upgrade head` automatically

---

## Step 2 – Upstash (Redis)

1. Go to https://upstash.com and sign up
2. Create a new Redis database (free tier)
3. Choose a region close to your Render backend
4. After creation, copy the REST API URL (format: `rediss://default:TOKEN@REGION.upstash.io:6379`)
5. Save this as `REDIS_URL` and `CELERY_BROKER_URL` environment variables

---

## Step 3 – Render (Backend API)

### Option A: Deploy via Git (Recommended)

1. Push your code to a GitHub repository
2. Go to https://render.com → **New Web Service**
3. Connect your GitHub repo
4. Configure:
   - **Name**: `gotot-api`
   - **Region**: Choose closest to your users
   - **Branch**: `main` (or your production branch)
   - **Runtime**: Docker
   - **Build Command**: (leave default - uses Dockerfile)
   - **Start Command**: (leave default - uses CMD from Dockerfile)
   - **Plan**: Free ($0/month)
5. Add all environment variables from `.env.production.template`
6. Click **Create Web Service**

### Option B: Deploy via Docker Registry

If you prefer to build locally and push:

```bash
docker build -t gotot-api ./backend
docker tag gotot-api registry.render.com/your-app/gotot-api
docker push registry.render.com/your-app/gotot-api
```

### Auto-Migrations

The backend Docker entrypoint (`docker-entrypoint.sh`) runs `alembic upgrade head` automatically on every deploy.

### Important Render Settings

- **Health Check Path**: `/health`
- **Auto-Deploy**: Yes (on git push)
- **Sleep**: Free tier sleeps after 15 min of inactivity. Consider upgrading to a paid plan for no sleeping.

---

## Step 4 – Vercel (Frontend)

The `vercel.json` file in the `frontend/` directory is pre-configured with rewrites to proxy `/api/*` to your Render backend.

1. Go to https://vercel.com and sign up
2. Click **Add New → Project**
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Next.js (auto-detected)
   - **Root Directory**: `frontend` (since your repo has both frontend and backend)
   - **Build Command**: `npm run build` (keep default)
   - **Output Directory**: `.next` (keep default)
5. Add Environment Variables:
   - `NEXT_PUBLIC_API_URL` → `/api`
   - `NEXT_PUBLIC_WS_URL` → `wss://gotot-api.onrender.com`
6. Click **Deploy**

### Update Rewrites

After deploying, update `vercel.json` to point to your actual Render backend URL:

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://YOUR-RENDER-APP-NAME.onrender.com/:path*"
    }
  ]
}
```

---

## Step 5 – Razorpay (Payments)

1. Go to https://razorpay.com and sign up
2. Complete KYC for a live account (or use test mode first)
3. Go to **Settings → API Keys** and generate a key pair
4. Create plans:
   - **Pro plan**: Create a subscription plan in Razorpay Dashboard
   - **Unlimited plan**: Create a subscription plan in Razorpay Dashboard
5. Save the key ID, secret, and plan IDs to Render env vars

---

## Step 6 – Google OAuth

1. Go to https://console.cloud.google.com
2. Create a new project or select existing
3. Go to **APIs & Services → Credentials**
4. Click **Create Credentials → OAuth 2.0 Client ID**
5. Application type: **Web application**
6. Authorized JavaScript origins:
   - `https://gotot.vercel.app`
   - `http://localhost:3000` (for dev)
7. Authorized redirect URIs:
   - `https://gotot.vercel.app/auth/google/callback`
8. Copy the **Client ID** and **Client Secret** to Render env vars

---

## Step 7 – Sentry (Error Monitoring)

1. Go to https://sentry.io and sign up
2. Create a new project → **Python (FastAPI)**
3. Copy the DSN (looks like `https://key@oXXXX.ingest.us.sentry.io/XXXX`)
4. Add `SENTRY_DSN` to Render env vars

---

## Step 8 – Google Analytics

1. Go to https://analytics.google.com
2. Create a new property for your domain
3. Copy the Measurement ID (e.g., `G-XXXXXXXXXX`)
4. Add the Google Analytics script to `frontend/src/app/layout.tsx`

---

## Step 9 – UptimeRobot (Monitoring)

1. Go to https://uptimerobot.com and sign up
2. Click **Add New Monitor**
3. Configure:
   - **Monitor Type**: HTTP(s)
   - **URL**: `https://gotot-api.onrender.com/health`
   - **Interval**: 5 minutes
   - **Alert Contacts**: Add your email
4. Create a second monitor for the frontend:
   - **URL**: `https://gotot.vercel.app`

---

## Step 10 – Domain & HTTPS

Both Vercel and Render provide:
- Automatic HTTPS via Let's Encrypt
- Free subdomains (`.vercel.app` and `.onrender.com`)

### Custom Domain (optional)

1. Buy a domain from any registrar
2. On Vercel: Go to project → **Settings → Domains** → Add your domain
3. On Render: Go to Web Service → **Settings → Custom Domain** → Add your domain
4. Configure DNS (CNAME records) as instructed

---

## Step 11 – SSL/TLS Verification

After deployment, verify:

```bash
# CORS headers
curl -I https://gotot.vercel.app

# API health
curl https://gotot-api.onrender.com/health

# Security headers
curl -sI https://gotot.vercel.app | grep -i "strict-transport-security"

# HTTPS redirect
curl -sI http://gotot.vercel.app | grep -i "301\|location"
```

---

## File Serving for Downloads

On Render free tier, downloaded files are stored ephemerally in `/tmp/downloads`.
Files persist only for the instance lifetime. To serve downloads:

1. The download endpoint saves files to `/tmp/downloads/`
2. The `/download/file/{filename}` endpoint reads and serves them
3. Files are automatically cleaned up after `FILE_RETENTION_HOURS` (default: 1 hour)

For production with larger files, consider:
- Cloudinary for storing and serving downloads
- AWS S3-compatible storage

---

## Celery / Queue

On Render free tier, only one process runs. If you need background workers:

1. **Upgrade Render** to a paid plan for multiple processes
2. **Or** Skip Celery and use synchronous downloads (the app handles both paths)
3. **Or** Use a separate Cron Job on Render for periodic tasks

The QueueProgress component falls back to polling if WebSocket connects fail.

---

## Backup Strategy

Supabase free tier includes:
- Point-in-time recovery
- Automatic daily backups (7-day retention)

Use the Supabase Dashboard to:
- Download backups
- Schedule manual exports

---

## Monitoring

| Tool | What It Monitors | URL |
|------|-----------------|-----|
| UptimeRobot | Frontend + Backend uptime | https://uptimerobot.com |
| Sentry | Backend errors + performance | https://sentry.io |
| Google Analytics | Frontend traffic + user behavior | https://analytics.google.com |
| Render Dashboard | Backend CPU/memory/logs | https://dashboard.render.com |
| Vercel Dashboard | Frontend build/deploy/analytics | https://vercel.com/dashboard |

---

## Troubleshooting

### Backend health check fails
```bash
# Check Render logs
# Verify DATABASE_URL is correct
# Run: curl https://gotot-api.onrender.com/health
```

### Frontend API calls return 404
```bash
# Check vercel.json rewrites destination URL
# Verify NEXT_PUBLIC_API_URL is set to /api
```

### CORS errors in browser
```bash
# Verify ALLOWED_ORIGINS includes your Vercel domain
# Format: https://gotot.vercel.app (no trailing slash)
```

### Database connection fails
```bash
# Verify Supabase project is active
# Check Supabase Dashboard > Database > Connection string
# Ensure password is URL-encoded (special chars replaced)
```

### WebSocket connection fails
```bash
# QueueProgress falls back to polling automatically
# Set NEXT_PUBLIC_WS_URL to your Render backend with wss:// protocol
```

---

## Environment Variables Checklist

### Render (Backend)

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | 64-char random string |
| `DATABASE_URL` | Yes | Supabase PostgreSQL connection string |
| `REDIS_URL` | Yes | Upstash Redis connection string |
| `ENVIRONMENT` | Yes | Set to `production` |
| `LOG_LEVEL` | Yes | `info` |
| `ALLOWED_ORIGINS` | Yes | Comma-separated Vercel URL(s) |
| `FRONTEND_URL` | Yes | Vercel deployment URL |
| `RAZORPAY_KEY_ID` | For payments | Razorpay live key |
| `RAZORPAY_KEY_SECRET` | For payments | Razorpay live secret |
| `SENTRY_DSN` | Recommended | Sentry error tracking |
| `SMTP_HOST` | For email | SMTP provider host |
| `SMTP_USER` | For email | SMTP username |
| `SMTP_PASSWORD` | For email | SMTP password |
| `SMTP_FROM_EMAIL` | For email | Sender email address |
| `ADMIN_EMAIL` | For email | Admin notification recipient |
| `GOOGLE_CLIENT_ID` | For Google Auth | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | For Google Auth | Google OAuth secret |
| `GOOGLE_REDIRECT_URI` | For Google Auth | `https://gotot.vercel.app/auth/google/callback` |

### Vercel (Frontend)

| Variable | Required | Value |
|----------|----------|-------|
| `NEXT_PUBLIC_API_URL` | Yes | `/api` |
| `NEXT_PUBLIC_WS_URL` | Yes | `wss://gotot-api.onrender.com` |
