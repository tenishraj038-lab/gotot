# GoTot - Universal Video Downloader

Download videos from YouTube, TikTok, Instagram, Twitter, Facebook, Reddit, Vimeo, Twitch, Dailymotion, LinkedIn, and Pinterest.

## Documentation

- [User Guide](USER_GUIDE.md)
- [Administrator Guide](ADMIN_GUIDE.md)
- [API Guide](API_GUIDE.md)
- [Developer Guide](DEVELOPER_GUIDE.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Backup Guide](BACKUP_GUIDE.md)
- [Recovery Guide](RECOVERY_GUIDE.md)
- [Architecture](ARCHITECTURE.md)
- [Database Schema](DATABASE.md)
- [Security](SECURITY.md)

## Quick Start

```bash
# Clone and run
git clone <repo> && cd gotot
cp backend/.env.example backend/.env
./run.sh production
```

## Tech Stack

- **Backend**: Python 3.12+ / FastAPI / SQLAlchemy async / Celery
- **Frontend**: Next.js 14 / TypeScript / Tailwind CSS / Zustand
- **Database**: PostgreSQL 16
- **Queue**: Redis + Celery
- **Payments**: Razorpay
- **Monitoring**: Prometheus
- **Proxy**: nginx

## License

Proprietary - All rights reserved.
