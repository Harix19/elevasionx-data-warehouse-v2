# Railway Deployment Guide - Contact Import Fix

## Step 1: Login to Railway CLI

```bash
railway login
```
This will open a browser window for authentication.

## Step 2: Create Railway Project

```bash
# Create new project
railway init

# Or if project exists, link to it
railway link
```

## Step 3: Add Services

### 3.1 Deploy Redis Service

In Railway Dashboard:
1. Click "New" → "Database" → "Add Redis"
2. Wait for Redis to deploy (takes ~1 minute)
3. Note: Redis URL will be auto-configured as `${{ redis.REDIS_URL }}`

### 3.2 Deploy Backend Service

**Option A: Via CLI**
```bash
cd /Users/harishkanna/projects/elevasionx-data-wearhouse/backend
railway up
```

**Option B: Via Dashboard**
1. Click "New" → "GitHub Repo"
2. Select `Harix19/elevasionx-data-warehouse-v2`
3. Configure service:
   - **Root Directory:** `/backend`
   - **Builder:** Nixpacks (auto-detected)
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Pre-deploy Command:** `alembic upgrade head`

### 3.3 Configure Backend Environment Variables

Add these variables in Railway Dashboard:

```
DATABASE_URL=postgresql://neondb_owner:npg_WZ2gwcNpfnC5@ep-blue-violet-ahgkv3ap-pooler.c-3.us-east-1.aws.neon.tech:6543/neondb?sslmode=require
REDIS_URL=${{ redis.REDIS_URL }}
SECRET_KEY=your-256-bit-secret-key-here-change-this-in-production
DEBUG=false
CACHE_ENABLED=true
CACHE_DEFAULT_TTL=300
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=1000
```

### 3.4 Deploy Frontend Service

**Option A: Via CLI**
```bash
cd /Users/harishkanna/projects/elevasionx-data-wearhouse/frontend
railway up
```

**Option B: Via Dashboard**
1. Click "New" → "GitHub Repo"
2. Select same repository
3. Configure service:
   - **Root Directory:** `/frontend`
   - **Builder:** Nixpacks (auto-detected)
   - **Start Command:** `next start --hostname :: --port ${PORT-3000}`

### 3.5 Configure Frontend Environment Variables

```
NEXT_PUBLIC_API_URL=https://${{ backend.RAILWAY_PUBLIC_DOMAIN }}/api/v1
NEXT_PUBLIC_APP_ENV=production
```

## Step 4: Verify Deployment

### Check Backend Health
```bash
curl https://<backend-domain>/health/ready
```
Expected: `{"status":"ready","checks":{"database":true,"redis":true,"cache":true}}`

### Check Database Migration
Migration runs automatically via `preDeployCommand` in `railway.toml`.
Verify columns exist:
```bash
railway run --service backend psql $DATABASE_URL -c "\d contacts" | grep -E "industry|country|city|state"
```

### Test Contact Import
1. Open frontend URL in browser
2. Navigate to Contacts → Import
3. Upload a sample CSV (Wellfound/Prospeo format)
4. Verify no 422 errors

## Step 5: Verify All Services

```bash
# Check all services status
railway status

# View logs
railway logs --service backend
railway logs --service frontend

# Check environment variables
railway variables --service backend
railway variables --service frontend
```

## Troubleshooting

### Migration Failed
```bash
# Run migration manually
railway run --service backend alembic upgrade head
```

### Redis Connection Failed
- Verify Redis service is running in Railway dashboard
- Check `REDIS_URL` is properly referenced
- Test: `railway run --service backend python -c "import redis; r = redis.from_url('$REDIS_URL'); print(r.ping())"`

### Backend Won't Start
- Check logs: `railway logs --service backend`
- Verify DATABASE_URL format (should use `postgresql://` not `postgresql+asyncpg://` for Railway)
- Ensure Neon PgBouncer port 6543 is used

## Service Architecture

```
┌─────────────────────────────────────────────┐
│           Railway Project                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Frontend │  │ Backend  │  │  Redis   │   │
│  │ Next.js  │  │ FastAPI  │  │  Cache   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │             │         │
│       └─────────────┴─────────────┘         │
│            Private Network                  │
└─────────────────────────────────────────────┘
              │
              │ External
              ▼
┌─────────────────────────────────────────────┐
│         Neon Serverless PostgreSQL          │
│              (PgBouncer 6543)                 │
└─────────────────────────────────────────────┘
```

## Post-Deployment Checklist

- [ ] All 3 services healthy in Railway dashboard
- [ ] Database migration completed (4 new columns in contacts)
- [ ] Redis connection working
- [ ] Frontend loads without errors
- [ ] Import Wellfound CSV successfully
- [ ] Import Prospeo CSV successfully
- [ ] All new fields (industry, country, city, state) stored correctly

## Quick Commands Reference

```bash
# Deploy all services
railway up

# Deploy specific service
railway up --service backend

# View service logs
railway logs --service <service-name>

# Shell into service
railway shell --service backend

# Run database commands
railway run --service backend alembic current
railway run --service backend alembic history

# Check Redis
railway run --service redis redis-cli ping
```

## Support

- Railway Docs: https://docs.railway.com/
- Railway Dashboard: https://railway.com/dashboard
- Neon Console: https://console.neon.tech/
