# GoTot Production Deployment Guide (Free Tier)

Estimated time: 15 minutes. Zero cost. All services remain free indefinitely.

---

## Prerequisites

- GitHub account (free)
- Cloudflare account (free)
- Render account (free — GitHub login works)
- Supabase account (free)
- Upstash account (free — GitHub login works)

---

## Step 1 — GitHub Repository

Create a **single** repository (not two — monorepo with `frontend/` and `backend/` folders):

```bash
cd gotot
git init
git add .
git commit -m "Production-ready deployment"
git remote add origin https://github.com/YOUR_USERNAME/gotot.git
git branch -M main
git push -u origin main
```

Verify `.gitignore` covers:
- `.env` (all levels)
- `.venv/`, `node_modules/`, `.next/`
- `*.pyc`, `__pycache__/`
- `nginx/ssl/`, `backups/`

**Never commit actual `.env` files or credentials.**

---

## Step 2 — Supabase (Database)

1. Go to [supabase.com](https://supabase.com) → New Project
2. Project name: `gotot`
3. Password: generate one, save it
4. Region: closest to Render region (Oregon / Frankfurt)
5. Wait for project to spin up (~1 minute)
6. Go to **Settings → Database → Connection string**
7. Copy the **URI** format (starts with `postgresql://postgres:`)
8. Replace `[YOUR-PASSWORD]` with your database password

Your `DATABASE_URL` looks like:
```
postgresql+asyncpg://postgres:YOUR_PASSWORD@db.XXXXXX.supabase.co:5432/postgres
```

Note the `+asyncpg` — Render uses async PostgreSQL.

**Migrations run automatically on Render startup** — no manual steps needed.

---

## Step 3 — Upstash (Redis)

1. Go to [upstash.com](https://upstash.com) → Create Redis Database
2. Name: `gotot`
3. Region: same as Render
4. Type: **Global** or **Regional**
5. Copy the **REST URL** (starts with `rediss://`)

Your `REDIS_URL` looks like:
```
rediss://default:YOUR_PASSWORD@us1-excited-griffon-12345.upstash.io:6379
```

---

## Step 4 — Render (Backend)

1. Go to [render.com](https://render.com) → New **Web Service**
2. Connect your GitHub repo
3. Settings:
   - **Name**: `gotot-api`
   - **Region**: Oregon
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`
   - **Plan**: Free

4. **Environment Variables** (Render dashboard → Environment):

| Key | Value |
|-----|-------|
| `ENVIRONMENT` | `production` |
| `SECRET_KEY` | Run: `openssl rand -hex 32` — paste the output |
| `DATABASE_URL` | Your Supabase URL from Step 2 |
| `REDIS_URL` | Your Upstash URL from Step 3 |
| `ALLOWED_ORIGINS` | `https://gotot.pages.dev` (placeholder — update after Step 5) |
| `FRONTEND_URL` | `https://gotot.pages.dev` (placeholder) |
| `LOG_LEVEL` | `info` |
| `RATE_LIMIT_PER_MINUTE` | `60` |
| `DOWNLOAD_TIMEOUT` | `300` |
| `CACHE_TTL` | `3600` |
| `FILE_RETENTION_HOURS` | `1` |
| `MAX_FILE_SIZE_MB` | `500` |
| `CURRENCY` | `USD` |

Optional (email, payments, Google OAuth) — add when needed:
| `RAZORPAY_KEY_ID` | From Razorpay Dashboard |
| `RAZORPAY_KEY_SECRET` | From Razorpay Dashboard |
| `SENTRY_DSN` | From sentry.io |
| `SMTP_HOST` | e.g. `smtp.sendgrid.net` |
| `GOOGLE_CLIENT_ID` | From Google Cloud Console |

5. Click **Create Web Service** — Render builds and deploys automatically.

---

## Step 5 — Cloudflare Pages (Frontend)

1. Go to [dash.cloudflare.com](https://dash.cloudflare.com) → Workers & Pages → Create → Pages
2. Connect your GitHub repo
3. Settings:
   - **Project name**: `gotot`
   - **Production branch**: `main`
   - **Build command**: `cd frontend && npm ci && npx next build`
   - **Build output directory**: `frontend/.next`
   - **Root directory**: `frontend`

4. **Environment Variables** (Cloudflare dashboard):

| Key | Value |
|-----|-------|
| `NODE_VERSION` | `20` |
| `NEXT_PUBLIC_API_URL` | `/api` |
| `BACKEND_API_URL` | Your Render URL from Step 4 (e.g. `https://gotot-api.onrender.com`) |

5. Click **Save and Deploy**.

Cloudflare Pages auto-assigns a domain: `https://gotot.pages.dev`

---

## Step 6 — Connect Frontend ↔ Backend

1. In Cloudflare Pages dashboard → gotot → Settings → Functions → **Workers Routes**:

   Add a Worker route:
   ```
   /api/* → proxy to https://gotot-api.onrender.com
   ```

   Create a `functions/api/_middleware.js` in the frontend repo:
   ```javascript
   // Cloudflare Pages Functions middleware — proxies /api/* to Render backend
   export async function onRequest(context) {
     const url = new URL(context.request.url);
     url.hostname = 'gotot-api.onrender.com';
     url.protocol = 'https:';
     return fetch(url.toString(), {
       method: context.request.method,
       headers: context.request.headers,
       body: context.request.method !== 'GET' ? await context.request.text() : undefined,
     });
   }
   ```

2. Update Render's `ALLOWED_ORIGINS` to your Cloudflare Pages domain:
   ```
   https://gotot.pages.dev
   ```
   And update `FRONTEND_URL` to the same.

3. Redeploy Render (or restart the service).

---

## Step 7 — Verify Deployment

### Backend Health Check
```bash
curl https://gotot-api.onrender.com/health
# Expected: {"status":"ok","environment":"production","database":"connected"}
```

### Frontend Loads
Open `https://gotot.pages.dev` in browser.

### API Proxy Works
```bash
curl https://gotot.pages.dev/api/health
# Expected: same as backend health response
```

### Platforms Endpoint
```bash
curl https://gotot.pages.dev/api/download/platforms
# Expected: list of 15 platforms
```

### Database Connected
Check Render logs for:
```
INFO:     Database initialized
```

---

## Step 8 — Cron Job (Keep Render Alive)

Render free tier spins down after 15 minutes of inactivity. Add a **GitHub Actions** cron to ping every 10 minutes:

`.github/workflows/keepalive.yml`:
```yaml
name: Keep Render Alive
on:
  schedule:
    - cron: '*/10 * * * *'
jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - run: curl -sf https://gotot-api.onrender.com/health
```

---

## Free Tier Limitations

| Service | Limit | Impact |
|---------|-------|--------|
| Render | 750 hrs/month, 15min idle spin-down | Cold start ~30s after idle |
| Render | 512MB RAM, 1GB disk (ephemeral) | Files auto-deleted, downloads temporary |
| Render | No persistent disk | Can't store downloads long-term |
| Supabase | 500MB database, 2 projects | Adequate for thousands of users |
| Supabase | Paused after 1 week inactivity | Keep pinging or use weekly |
| Upstash | 10,000 commands/day | ~14 req/min average |
| Cloudflare Pages | 500 builds/month, 100K requests/day | Scales well |
| Cloudflare Pages | 25MB per Worker | Sufficient for API proxy |

---

## Production URLs

| Service | URL |
|---------|-----|
| Frontend | `https://gotot.pages.dev` |
| Backend API | `https://gotot-api.onrender.com` |
| API Docs | `https://gotot-api.onrender.com/docs` |

---

## Security Verification Checklist

- [x] HTTPS on both frontend and backend
- [x] Security headers (HSTS, CSP, X-Frame-Options, etc.)
- [x] CORS restricted to frontend origin
- [x] Rate limiting (slowapi, 60 req/min)
- [x] CSRF protection (production mode)
- [x] Input validation (Pydantic validators)
- [x] URL sanitization (SSRF protection)
- [x] `.env` gitignored — zero secrets in repo
- [x] No debug mode in production
- [x] Cookie consent banner (GA gated)
- [x] Terms of Service, Privacy Policy, DMCA, Copyright pages

---

## Rollback

If something breaks:
1. Go to Render → gotot-api → Deploys → click the previous deploy → **Rollback**
2. Go to Cloudflare Pages → gotot → Deployments → click the previous deploy → **Rollback**

---

## Troubleshooting

**Backend won't start**: Check Render logs → ensure `DATABASE_URL` format includes `+asyncpg`

**Database connection fails**: Verify Supabase isn't paused (login to dashboard), check connection string

**CORS errors**: Verify `ALLOWED_ORIGINS` on Render matches your Cloudflare Pages domain exactly

**Downloads take too long**: Render free has 512MB RAM — large 4K downloads may OOM. Use lower quality or upgrade to Render Starter ($7/mo)
