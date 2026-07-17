# GoTot User Guide

GoTot is a universal video downloader supporting 11+ platforms including YouTube, TikTok, Instagram, Twitter/X, Facebook, Reddit, Vimeo, Twitch, Dailymotion, LinkedIn, and Pinterest. Download videos in MP4, WebM, 3GP, or extract MP3 audio — all from your browser.

---

## Table of Contents

- [Creating an Account](#creating-an-account)
- [Downloading Videos](#downloading-videos)
- [Batch Downloads & Playlists](#batch-downloads--playlists)
- [Download History & Search](#download-history--search)
- [Subscription Plans](#subscription-plans)
- [Referral Program](#referral-program)
- [API Keys](#api-keys)
- [Managing Your Account](#managing-your-account)
- [PWA Installation](#pwa-installation)
- [Supported Platforms](#supported-platforms)
- [Troubleshooting](#troubleshooting)

---

## Creating an Account

You can download videos **without an account**. However, creating one unlocks history, subscriptions, API access, and referral rewards.

### Register

1. Click **Sign In** in the top-right corner.
2. Select the **Register** tab.
3. Enter:
   - **Email** — a valid email address
   - **Username** — 3+ alphanumeric characters
   - **Password** — 8+ characters, at least one uppercase letter and one digit
4. Click **Create Account**.

You are logged in immediately after registration.

### Google Sign-In

1. Click **Sign In**, then select **Continue with Google**.
2. Authorize GoTot with your Google account.
3. A new account is created automatically if one doesn't exist.

### Login

Use your email and password on the **Sign In** tab.

---

## Downloading Videos

### Quick Download (No Account)

1. Go to the [homepage](https://gotot.app).
2. Paste a video URL into the download box.
3. Click **Get Video**.
4. Wait for video analysis to complete.
5. Select your preferred **format** and **quality**.
6. Click **Download** to save the file.

### Format Selection

After analysis, you'll see all available formats organized in tabs:

| Tab | Options |
|-----|---------|
| **Video** | MP4, WebM, 3GP in various resolutions (360p, 720p, 1080p, 4K) |
| **Audio** | MP3 extraction with bitrate: 128kbps, 192kbps, 256kbps, 320kbps |

Click **Show all N formats** to see every available option, including video-only and audio-only streams.

### Quality Options

Available qualities depend on the source video and platform:

- **Free tier**: All qualities available
- **Min**: 360p (lowest)
- **Max**: 4K (2160p) where supported
- **Audio only**: M4A or MP3

### Platform Detection

When you paste a URL, GoTot automatically detects the platform and shows a badge (e.g., "YouTube detected"). This confirms the URL is supported before analysis.

### Sharing

After a successful download, use the **Share** button to send the video title and link via WhatsApp, Twitter/X, Facebook, or copy the link to your clipboard.

---

## Batch Downloads & Playlists

### Batch Download

Download up to **20 videos at once**:

1. Click the **Batch** tab in the download area.
2. Paste multiple URLs (one per line, or comma-separated).
3. Select a format/quality to apply to all.
4. Click **Download All**.

Results show each URL with success/error status and file details.

### Playlist Download

When you paste a playlist URL, GoTot detects it automatically:

1. The **Playlist Viewer** opens showing all videos in the playlist.
2. Check/uncheck individual videos or use **Select All** / **Clear Selection**.
3. Click **Download Selected (N)** to download checked items.
4. Each video is downloaded individually.

---

## Download History & Search

### History (Authenticated Users)

1. Go to your **Dashboard** > **History**.
2. View all past downloads with title, platform, format, size, and date.
3. Filter by platform or search by URL.

### Search History

Use the search bar on the **History** page to find past downloads by URL or title.

### Recent Downloads (Public)

The homepage shows recent public downloads (platform, format, size, and time only — no URLs or user data).

---

## Subscription Plans

GoTot offers three tiers:

| Feature | Free | Pro ($4.99/mo) | Unlimited ($9.99/mo) |
|---------|------|-----------------|-----------------------|
| Daily downloads | Unlimited | 100 | 1,000 |
| Max quality | 4K | 4K | 4K |
| MP3 extraction | Yes | Yes | Yes |
| Batch downloads | Yes (20) | Yes (20) | Yes (20) |
| API access | Limited (2 keys) | Full | Full |
| Concurrent downloads | 1 | 3 | 10 |
| Ads | Optional | None | None |
| Priority support | No | No | Yes |

### Upgrading

1. Go to **Pricing** or **Dashboard** > **Billing**.
2. Choose **Pro** or **Unlimited**.
3. Click **Upgrade Now**.
4. Complete payment via Razorpay (credit/debit card, UPI, net banking, wallets).
5. Your account upgrades immediately.

### Cancelling

1. Go to **Dashboard** > **Billing**.
2. Click **Cancel Subscription**.
3. Your subscription remains active until the end of the billing period.
4. After expiry, your account reverts to Free tier.

---

## Referral Program

Earn bonus downloads by inviting friends.

### How It Works

- Each successful referral gives you **+3 bonus downloads** added to your daily limit.
- Your friend also gets the same benefit.

### Getting Your Referral Code

1. Go to **Dashboard** > **Referrals**.
2. Your unique referral code (e.g., `GOTOTABC123`) and shareable link are displayed.
3. Share the link or code with friends.

### Applying a Referral Code

1. Go to **Dashboard** > **Referrals**.
2. Enter a friend's referral code.
3. Click **Apply**.
4. You immediately receive +3 bonus downloads.

### Referral Stats

The referrals page shows:
- Total referred users
- Referrals this week / month
- Pending referrals
- Total credits earned
- Your rank on the leaderboard

### Leaderboard

The referral leaderboard shows top referrers globally, weekly, and monthly. Badges are awarded:
- **Gold** (#1), **Silver** (#2), **Bronze** (#3)
- **Top 10**, **Top 50**, **Top 100**

---

## API Keys

API keys allow programmatic access to GoTot's download engine.

### Creating an API Key

1. Go to **Dashboard** > **API Keys**.
2. Click **Create New Key**.
3. Enter a name for the key.
4. The full key is shown once — copy and store it securely.

### Rate Limits by Tier

| Tier | Daily Limit | Max Keys |
|------|------------|----------|
| Free | 50 requests | 2 keys |
| Pro | 1,000 requests | Unlimited |
| Unlimited | 10,000 requests | Unlimited |

### Using an API Key

Include the key in the `X-API-Key` header:

```
curl -H "X-API-Key: gt_abc123..." https://gotot.app/api/download/info
  -d '{"url": "https://youtube.com/watch?v=..."}'
```

### Revoking an API Key

1. Go to **Dashboard** > **API Keys**.
2. Find the key and click **Revoke**.
3. The key is immediately deactivated.

---

## Managing Your Account

### Dashboard

Accessible at `/dashboard`, it shows:
- Current plan and daily download usage
- Recent download activity
- Quick links to billing, API keys, and referrals

### Settings

Go to **Dashboard** > **Settings** to:
- Change your username
- Update email preferences (notifications, marketing)
- View account details

### Billing

Go to **Dashboard** > **Billing** to:
- View current subscription status
- Upgrade or cancel your plan
- View payment history

### Change Password

1. Go to **Dashboard** > **Settings**.
2. Enter your current password and new password.
3. Click **Save**. You'll receive new tokens and be redirected.

### Email Preferences

Control which emails you receive:
- Security alerts
- Product updates
- Marketing / referral notifications

---

## PWA Installation

GoTot is a Progressive Web App (PWA) that can be installed on your device for a native-like experience.

### Desktop (Chrome, Edge, Brave)

1. Open [gotot.app](https://gotot.app).
2. Click the install icon in the address bar (or use the menu > **Install GoTot**).
3. Click **Install**.

### Mobile (Android)

1. Open [gotot.app](https://gotot.app) in Chrome.
2. Tap the menu (three dots) > **Add to Home Screen**.
3. Tap **Add**.

### iOS (Safari)

1. Open [gotot.app](https://gotot.app) in Safari.
2. Tap the **Share** button.
3. Scroll down and tap **Add to Home Screen**.
4. Tap **Add**.

---

## Supported Platforms

| Platform | URLs | Formats |
|----------|------|---------|
| **YouTube** | `youtube.com/*`, `youtu.be/*`, shorts | MP4, WebM, M4A, MP3 |
| **TikTok** | `tiktok.com/*` | MP4, MP3 |
| **Instagram** | `instagram.com/p/*`, reels, stories | MP4, MP3 |
| **Twitter/X** | `twitter.com/*`, `x.com/*` | MP4, MP3 |
| **Facebook** | `facebook.com/*`, `fb.watch/*` | MP4, MP3 |
| **Reddit** | `reddit.com/r/*`, `redd.it/*` | MP4 |
| **Vimeo** | `vimeo.com/*` | MP4, MP3 |
| **Twitch** | `twitch.tv/*`, clips | MP4, MP3 |
| **Dailymotion** | `dailymotion.com/*`, `dai.ly/*` | MP4, MP3 |
| **LinkedIn** | `linkedin.com/feed/*`, `linkedin.com/events/*` | MP4 |
| **Pinterest** | `pinterest.com/*`, `pin.it/*` | MP4, MP3 |

---

## Troubleshooting

### "Could not extract video info"

- Verify the URL is correct and the video is publicly accessible.
- Some private or age-restricted videos cannot be downloaded.
- The platform may have rate-limited downloads. Try again later.

### "Unsupported platform"

- Check that the URL belongs to one of the 11 supported platforms.
- Shortened URLs (e.g., bit.ly) are not recognized — paste the direct URL.

### Download fails midway

- Large downloads may timeout on slow connections. Try a lower quality.
- The file retention period is 1 hour — complete your download promptly.

### "Daily download limit reached"

- Wait for the daily reset (midnight UTC) or upgrade to Pro/Unlimited.

### File not found when downloading

- Downloaded files are stored temporarily and removed after 1 hour.
- Redownload the video if the link has expired.

### Slow download speeds

- Download speeds depend on the source platform's CDN and your connection.
- Try a lower resolution for faster downloads.

### Payment failed

- Ensure your card/internet banking supports international transactions.
- Contact your bank if Razorpay payments are blocked.
- Try an alternative payment method (UPI, wallet).

### Account locked / "Account is deactivated"

- Contact support at [support@gotot.app](mailto:support@gotot.app) if you believe this was an error.

### Cookie/CSRF errors

- Clear your browser cookies and cache, then try again.
- Ensure cookies are enabled in your browser settings.

### Still need help?

Reach out via the [Contact form](https://gotot.app/contact) or email **support@gotot.app**. We typically respond within 24 hours.
