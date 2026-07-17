# GoToT Final Launch Checklist

## Pre-Launch

### Infrastructure
- [ ] Supabase PostgreSQL provisioned and running
- [ ] Upstash Redis provisioned and running
- [ ] Backend deployed on Render Web Service
- [ ] Frontend deployed on Vercel
- [ ] Database migrations run (`alembic upgrade head`)
- [ ] Health endpoint responds `200 OK`

### Configuration
- [ ] `SECRET_KEY` set to 64-char random value on Render
- [ ] `DATABASE_URL` configured with Supabase credentials
- [ ] `REDIS_URL` configured with Upstash credentials
- [ ] `ALLOWED_ORIGINS` includes Vercel frontend URL
- [ ] `FRONTEND_URL` set to Vercel frontend URL
- [ ] `NEXT_PUBLIC_API_URL=/api` set on Vercel
- [ ] `NEXT_PUBLIC_WS_URL` set to Render WebSocket URL on Vercel
- [ ] `vercel.json` rewrites point to correct Render URL
- [ ] `.env` file is NOT committed to git

### Security
- [ ] HTTPS enabled on both Vercel and Render
- [ ] HSTS headers present (Strict-Transport-Security)
- [ ] CSRF protection active (ENVIRONMENT=production)
- [ ] CORS configured correctly (only frontend domain allowed)
- [ ] Rate limiting enabled (100 req/min default)
- [ ] All secrets are strong and unique

### External Services
- [ ] Razorpay account active (test or live)
- [ ] Razorpay API keys configured
- [ ] Razorpay subscription plans created (Pro + Unlimited)
- [ ] Razorpay webhook secret set
- [ ] Google OAuth credentials created
- [ ] Google OAuth redirect URIs configured
- [ ] SMTP provider configured (SendGrid / Mailgun)
- [ ] Sentry DSN configured for error tracking

---

## Functional Verification

### Homepage
- [ ] Loads in < 3 seconds
- [ ] Hero section renders with CTA
- [ ] Features section renders
- [ ] Pricing section renders
- [ ] Footer renders with all links
- [ ] Mobile responsive layout works
- [ ] Dark mode toggle works

### Authentication
- [ ] User registration works
- [ ] Login with email/password works
- [ ] Login with Google OAuth works
- [ ] Password reset flow works
- [ ] Token refresh works
- [ ] Session persists across page reloads
- [ ] Logout clears session

### Downloads
- [ ] Enter YouTube URL and fetch video info
- [ ] Select format and start download
- [ ] MP3 conversion works
- [ ] Batch download works (up to 20 URLs)
- [ ] Playlist extraction works
- [ ] Download history displays correctly
- [ ] Download file serving works (authenticated)
- [ ] Downloads from TikTok work
- [ ] Downloads from Instagram work
- [ ] Downloads from Twitter/X work
- [ ] Downloads from Facebook work
- [ ] Downloads from Reddit work
- [ ] Downloads from Vimeo work
- [ ] Downloads from Twitch work
- [ ] Downloads from Dailymotion work
- [ ] Downloads from LinkedIn work
- [ ] Downloads from Pinterest work

### Queue System
- [ ] Queue download creates task
- [ ] WebSocket progress updates work
- [ ] Polling fallback works when WebSocket unavailable
- [ ] Queue status page shows pending/processing/completed/failed
- [ ] Task completion notification fires

### Notifications
- [ ] Notification bell shows unread count
- [ ] Notification list page works
- [ ] Mark as read works
- [ ] Mark all as read works
- [ ] Real-time updates work (30s polling)

### Billing / Payments
- [ ] Subscription checkout page loads
- [ ] Razorpay payment flow works (test mode)
- [ ] Payment success redirect works
- [ ] Payment history table loads
- [ ] Cancel subscription works
- [ ] Billing dashboard shows current plan

### Referral System
- [ ] Referral code is generated
- [ ] Referral leaderboard displays correctly
- [ ] Apply referral code works
- [ ] Referral stats show correct data
- [ ] Referral history page works

### Settings / Profile
- [ ] Profile tab displays user info
- [ ] Username update works
- [ ] Password change works
- [ ] Notification preferences toggle works

### Admin Panel
- [ ] Admin login works
- [ ] Overview tab shows stats
- [ ] Users tab lists users
- [ ] Subscriptions tab works
- [ ] Feature flags create/toggle works
- [ ] System health check works
- [ ] Analytics tab shows charts
- [ ] Affiliates CRUD works
- [ ] Queue status tab works
- [ ] Audit logs tab shows log entries

### API
- [ ] API docs portal loads (`/docs`)
- [ ] API key creation works
- [ ] API key authentication works
- [ ] Rate limiting works for API keys
- [ ] All documented endpoints respond correctly

### Help & Feedback
- [ ] Contact form submits successfully
- [ ] Bug report form works
- [ ] Feature request form works
- [ ] Satisfaction survey submits
- [ ] Newsletter signup in footer works

---

## SEO & PWA Verification

### SEO
- [ ] Page title and description render correctly
- [ ] Open Graph meta tags present
- [ ] Twitter card meta tags present
- [ ] Structured data (JSON-LD) present on homepage
- [ ] `robots.txt` accessible
- [ ] `sitemap.xml` accessible and valid
- [ ] Canonical URL set correctly
- [ ] Semantic HTML structure

### PWA
- [ ] `manifest.json` loads correctly
- [ ] Service worker registers without errors
- [ ] Offline page renders when offline
- [ ] App install prompt works (on supported browsers)
- [ ] Theme color and background color render correctly
- [ ] Icons load at all sizes (72x72 through 512x512)

---

## Performance & Security

### Performance
- [ ] Lighthouse score ≥ 90 (Desktop)
- [ ] Lighthouse score ≥ 70 (Mobile)
- [ ] Core Web Vitals pass (LCP < 2.5s, FID < 100ms, CLS < 0.1)
- [ ] Images are optimized (WebP/AVIF)
- [ ] JavaScript bundles are code-split
- [ ] Font loading optimized
- [ ] First Contentful Paint (FCP) < 1.5s

### Security
- [ ] No secrets exposed in client-side code
- [ ] API rate limiting active
- [ ] SQL injection protections (ORM queries)
- [ ] XSS protections (CSP headers)
- [ ] CSRF tokens validated for mutations
- [ ] Password strength enforcement
- [ ] HTTPS enforced (HTTP → 301 → HTTPS)
- [ ] Security headers present (HSTS, X-Frame-Options, etc.)
- [ ] Sentry capturing backend errors

---

## Monitoring & Alerts

### Monitoring
- [ ] UptimeRobot monitors frontend URL
- [ ] UptimeRobot monitors backend health endpoint
- [ ] Sentry captures backend exceptions
- [ ] Sentry captures frontend errors
- [ ] Google Analytics tracking code installed
- [ ] Render dashboard shows logs streaming

### Alerting
- [ ] Email alerts configured for downtime
- [ ] Sentry alerts for critical errors
- [ ] Razorpay webhook handling verified

---

## Post-Launch

### Rollback Plan
- [ ] Previous working version tagged in git
- [ ] Vercel instant rollback available (Deployments → Last Known Good)
- [ ] Render manual deploy to previous image possible
- [ ] Database backup downloaded before launch

### Launch Day
- [ ] Deploy during low-traffic hours
- [ ] Monitor Sentry for 1 hour post-launch
- [ ] Check UptimeRobot for 24 hours
- [ ] Test all core flows one more time
- [ ] Announce launch on social channels

### Post-Launch (Week 1)
- [ ] Monitor error rates daily
- [ ] Check database performance
- [ ] Review user feedback from contact/help forms
- [ ] Verify email delivery (welcome, password reset)
- [ ] Check payment success rate

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Developer | | | |
| QA | | | |
| Product | | | |

---

## Launch Decision

- [ ] All critical checklist items verified
- [ ] GoToT is ready for production launch
- [ ] Launch date: __________________
