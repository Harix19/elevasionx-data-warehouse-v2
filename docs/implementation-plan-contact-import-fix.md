# Implementation Plan: Contact Import Schema Update

**Date:** February 3, 2026  
**Status:** Implementation Complete - Pending Railway Deployment  
**Priority:** High  
**Deployment Target:** Railway Platform

---

## Problem Statement

The contact import feature fails with a 422 (Unprocessable Content) error when uploading real-world CSV files from sources like:
- Wellfound exports
- Prospeo person exports
- Staffing agency lead lists

### Root Causes

1. **Frontend sends invalid fields:** The `transformData()` function sends `keywords` and `technologies` fields for contacts, but these don't exist in the backend `BulkContactRecord` schema.

2. **Missing field aliases:** Real-world CSV column names (e.g., "Work Email", "Person LinkedIn URL", "organization_name") don't match the expected aliases in `CONTACT_FIELDS`.

3. **Missing database fields:** Important data from CSVs (industry, country, city, state) cannot be stored because the Contact model lacks these columns.

---

## Scope

### New Database Fields to Add
| Field | Type | Nullable | Description | Status |
|-------|------|----------|-------------|--------|
| `industry` | String | Yes | Industry sector (e.g., "staffing & recruiting") | ✅ Added |
| `country` | String | Yes | Contact's country | ✅ Added |
| `city` | String | Yes | Contact's city | ✅ Added |
| `state` | String | Yes | Contact's state/province | ✅ Added |

### Files Modified

| File | Type | Changes | Status |
|------|------|---------|--------|
| `backend/app/models/contact.py` | Model | Add 4 new columns | ✅ Complete |
| `backend/app/schemas/bulk.py` | Schema | Add 4 new fields to `BulkContactRecord` | ✅ Complete |
| `backend/app/services/bulk_service.py` | Service | Add new fields to upsert `set_=` dict | ✅ Complete |
| `frontend/lib/import-utils.ts` | Utils | Add new fields + update aliases | ✅ Complete |
| `frontend/lib/import-utils.ts` | Utils | Fix `transformData()` to exclude company-only fields | ✅ Complete |
| Alembic migration | Migration | Add new columns to contacts table | ✅ Complete |

---

## Infrastructure Context (Railway Deployment)

### Target Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Railway Project                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Frontend   │  │    Backend   │  │    Redis     │       │
│  │   Service    │  │    Service   │  │    Service   │       │
│  │  (Next.js)   │  │   (FastAPI)  │  │   (Template) │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                 │                │
│         └─────────────────┴─────────────────┘                │
│              Private Network (railway.internal)                │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ External (internet)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Neon Serverless                          │
│              (PostgreSQL with PgBouncer)                    │
│                   (port 6543 - pooled)                      │
└─────────────────────────────────────────────────────────────┘
```

### Key Railway Features to Leverage

1. **Private Networking**: Services communicate via `{service-name}.railway.internal` with microsecond latency
2. **Reference Variables**: Use `${{ service.VAR }}` syntax for cross-service configuration
3. **Redis Template**: One-click deploy with auto-configured environment variables
4. **Monorepo Support**: Deploy backend and frontend from same repo with different root directories

### Environment Variables for Railway

**Backend Service Variables:**
```bash
# Database (Neon Serverless - external to Railway)
DATABASE_URL=postgresql+asyncpg://user:pass@host.neon.tech:6543/dbname?ssl=require

# Redis (via Railway template - auto-populated reference)
REDIS_URL=${{ redis.REDIS_URL }}
CACHE_ENABLED=true
CACHE_DEFAULT_TTL=300

# Security
SECRET_KEY=${{ shared.SECRET_KEY }}
DEBUG=false

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=1000
```

**Frontend Service Variables:**
```bash
NEXT_PUBLIC_API_URL=https://${{ backend.RAILWAY_PUBLIC_DOMAIN }}/api/v1
NEXT_PUBLIC_APP_ENV=production
```

---

## Implementation Steps

### Step 1: Backend Model Update

**File:** `backend/app/models/contact.py`

**Action:** Add new columns after existing fields (around line 30):

```python
# New geographic/demographic fields
industry = Column(String, nullable=True)
country = Column(String, nullable=True)
city = Column(String, nullable=True)
state = Column(String, nullable=True)
```

**Placement:** After `company_linkedin_url` column, before `custom_tags_a`.

---

### Step 2: Backend Schema Update

**File:** `backend/app/schemas/bulk.py`

**Action:** Add new fields to `BulkContactRecord` class (around line 70):

```python
# New fields
industry: str | None = None
country: str | None = None
city: str | None = None
state: str | None = None
```

**Placement:** After `company_linkedin_url`, before `custom_tags_a`.

---

### Step 3: Bulk Service Update

**File:** `backend/app/services/bulk_service.py`

**Action:** Add new fields to the `set_=` dictionary in the `_upsert_contacts_batch` function.

**Location:** Find the `set_=` dict in the upsert statement and add:

```python
"industry": insert_stmt.excluded.industry,
"country": insert_stmt.excluded.country,
"city": insert_stmt.excluded.city,
"state": insert_stmt.excluded.state,
```

---

### Step 4: Database Migration

**Commands:**
```bash
cd backend
alembic revision --autogenerate -m "add industry country city state to contacts"
alembic upgrade head
```

**Expected Migration:** Creates 4 new nullable String columns in the `contacts` table.

**Railway Deployment Note:** Migration runs during deployment via `preDeployCommand` in `railway.toml`:
```toml
[deploy]
preDeployCommand = ["alembic upgrade head"]
```

---

### Step 5: Frontend Field Definitions Update

**File:** `frontend/lib/import-utils.ts`

**Action 1:** Update existing `CONTACT_FIELDS` with comprehensive aliases:

| Field Key | New Aliases to Add |
|-----------|-------------------|
| `email` | `work email` |
| `phone` | `phone number`, `mobile` |
| `job_title` | `job title` |
| `company_domain` | `organization_website_url`, `organization website url` |
| `working_company_name` | `organization_name`, `organization name`, `organization` |
| `linkedin_url` | `linkedin profile`, `person linkedin url`, `linkedin url` |
| `company_linkedin_url` | `organization_linkedin_url`, `organization linkedin url` |
| `seniority_level` | `seniority`, `job seniority` |
| `department` | `job department` |

**Action 2:** Add new field definitions:

```typescript
{ key: 'industry', label: 'Industry', aliases: ['sector', 'vertical'] },
{ key: 'country', label: 'Country', aliases: ['person country'] },
{ key: 'city', label: 'City', aliases: ['person city'] },
{ key: 'state', label: 'State', aliases: ['person state'] },
```

---

### Step 6: Frontend Transform Fix (Already Partially Done)

**File:** `frontend/lib/import-utils.ts`

**Action:** Ensure `transformData()` function:
1. Accepts `importType` parameter ✅ (already done)
2. Only initializes `keywords`/`technologies` for companies ✅ (already done)
3. Skips processing company-only fields for contacts ✅ (already done)

---

## Execution Order

```
1. Backend Model (contact.py)
   ↓
2. Backend Schema (bulk.py)
   ↓
3. Backend Service (bulk_service.py)
   ↓
4. Database Migration (alembic)
   ↓
5. Frontend Fields (import-utils.ts)
   ↓
6. Railway Configuration (railway.toml)
   ↓
7. Testing
```

---

## Railway Deployment Configuration

### Backend railway.toml

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
preDeployCommand = ["alembic upgrade head"]
healthcheckPath = "/health/ready"
healthcheckTimeout = 30
restartPolicyType = "on-failure"
restartPolicyMaxRetries = 3
```

### Frontend railway.toml

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "next start --hostname :: --port ${PORT-3000}"
healthcheckPath = "/"
healthcheckTimeout = 30
```

### Service Configuration

1. **Backend Service:**
   - Root directory: `/backend`
   - Environment variables: Reference Neon DB and Redis service

2. **Frontend Service:**
   - Root directory: `/frontend`
   - Environment variables: Reference backend public domain

3. **Redis Service:**
   - Deploy from Railway Redis template
   - Auto-configures REDIS_URL, REDISHOST, REDISPORT, REDISPASSWORD

---

## Testing Plan

### Code Implementation Tests ✅
- [x] Verify `BulkContactRecord` accepts new fields
- [x] Verify `BulkContactRecord` rejects unknown fields (like `keywords` for contacts)
- [x] Check backend model has all 4 new columns
- [x] Verify frontend field aliases are correct

### Pending Testing (After Railway Deploy)
- [ ] Import Wellfound CSV successfully
- [ ] Import Prospeo CSV successfully
- [ ] Import Staffing Agencies CSV successfully
- [ ] Verify new fields are stored in database
- [ ] Verify auto-mapping works for common column names
- [ ] Verify private networking (backend → Redis communication)
- [ ] Verify Redis connection via internal DNS
- [ ] Test database migration runs on deploy
- [ ] Verify health check endpoints

### Manual Testing (Pending)
1. Upload each sample CSV file
2. Verify column auto-mapping suggestions
3. Complete import without 422 error
4. Check database for imported records with all fields populated

---

## Sample CSV Column Mappings

### Wellfound Export
| CSV Column | Maps To |
|------------|---------|
| First Name | `first_name` |
| Last Name | `last_name` |
| Full Name | `full_name` |
| Job Title | `job_title` |
| Location | `location` |
| Company Domain | `company_domain` |
| LinkedIn Profile | `linkedin_url` |
| Work Email | `email` |

### Prospeo Export
| CSV Column | Maps To |
|------------|---------|
| First name | `first_name` |
| Last name | `last_name` |
| Full name | `full_name` |
| Person LinkedIn URL | `linkedin_url` |
| Email | `email` |
| Mobile | `phone` |
| Job title | `job_title` |
| Job department | `department` |
| Job seniority | `seniority_level` |
| Person country | `country` |
| Person state | `state` |
| Person city | `city` |

### Staffing Agencies Export
| CSV Column | Maps To |
|------------|---------|
| first_name | `first_name` |
| last_name | `last_name` |
| organization_name | `working_company_name` |
| Phone Number | `phone` |
| organization_website_url | `company_domain` |
| linkedin_url | `linkedin_url` |
| title | `job_title` |
| industry | `industry` |
| seniority | `seniority_level` |
| city | `city` |
| state | `state` |
| country | `country` |
| organization_linkedin_url | `company_linkedin_url` |

---

## Rollback Plan

If issues arise:
1. Run `alembic downgrade -1` to revert migration
2. Revert code changes via git
3. Restart backend service via Railway dashboard
4. If Railway deployment fails, use Railway's built-in rollback feature

---

## Implementation Summary

**Status:** ✅ Code changes complete, pending Railway deployment

| Task | Estimated | Actual | Status |
|------|-----------|--------|--------|
| Backend Model Update | 15 min | 5 min | ✅ Complete |
| Backend Schema Update | 10 min | 5 min | ✅ Complete |
| Backend Service Update | 10 min | 5 min | ✅ Complete |
| Database Migration | 5 min | 10 min | ✅ Complete (cleaned) |
| Frontend Field Updates | 20 min | 5 min | ✅ Complete |
| Railway Configuration | 30 min | In progress | ⏳ Pending |
| Testing | 30 min | - | ⏳ Pending |
| **Total** | ~1.5 hours | ~30 min + deploy | - |

### What Was Fixed

1. **Database Schema** - Added `industry`, `country`, `city`, `state` columns to `contacts` table
2. **Backend API** - `BulkContactRecord` now accepts these fields and bulk import properly upserts them
3. **Frontend** - CSV auto-mapping now recognizes:
   - Wellfound column names ("Work Email", "LinkedIn Profile")
   - Prospeo column names ("Person country", "Person city", "Person state")
   - Staffing agency columns ("organization_name", "industry", "seniority")

### Next Steps

1. Create `railway.toml` configuration files
2. Run database migration locally to verify
3. Deploy to Railway
4. Test with sample CSV imports

### Files Changed

```
backend/app/models/contact.py                    # Added 4 columns
backend/app/schemas/bulk.py                      # Added 4 fields to BulkContactRecord
backend/app/services/bulk_service.py             # Added fields to upsert logic
backend/alembic/versions/b269f2a46216_add_...    # Migration (cleaned up)
frontend/lib/import-utils.ts                     # Added aliases and field definitions
```

---

## Dependencies

- Alembic installed and configured
- Database access for migrations (Neon)
- Backend and frontend dev servers running for testing
- Railway CLI installed for deployment: `npm i -g @railway/cli`
- Railway project created and linked

---

## Related Documentation

- [Speed Optimization PRD](./Speed_Optimization_PRD.md)
- [Speed Optimization TODO](./Speed_Optimization_TODO.md)
- [Railway Documentation](https://docs.railway.com/)
- [Neon Serverless PostgreSQL](https://neon.tech/)

---

**Maintained by:** Engineering Team  
**Last Updated:** February 2026  
**Status:** Ready for Implementation
