# Implementation Plan: Contact Import Schema Update

**Date:** January 31, 2026  
**Status:** Pending  
**Priority:** High  

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
| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `industry` | String | Yes | Industry sector (e.g., "staffing & recruiting") |
| `country` | String | Yes | Contact's country |
| `city` | String | Yes | Contact's city |
| `state` | String | Yes | Contact's state/province |

### Files to Modify

| File | Type | Changes Required |
|------|------|------------------|
| `backend/app/models/contact.py` | Model | Add 4 new columns |
| `backend/app/schemas/bulk.py` | Schema | Add 4 new fields to `BulkContactRecord` |
| `backend/app/services/bulk_service.py` | Service | Add new fields to upsert `set_=` dict |
| `frontend/lib/import-utils.ts` | Utils | Add new fields + update aliases |
| `frontend/lib/import-utils.ts` | Utils | Fix `transformData()` to exclude company-only fields |
| Alembic migration | Migration | Add new columns to contacts table |

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
6. Testing
```

---

## Testing Plan

### Unit Tests
- [ ] Test `BulkContactRecord` accepts new fields
- [ ] Test `BulkContactRecord` rejects unknown fields (like `keywords` for contacts)

### Integration Tests
- [ ] Import Wellfound CSV successfully
- [ ] Import Prospeo CSV successfully
- [ ] Import Staffing Agencies CSV successfully
- [ ] Verify new fields are stored in database
- [ ] Verify auto-mapping works for common column names

### Manual Testing
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
3. Restart backend service

---

## Estimated Time

| Task | Time |
|------|------|
| Backend changes | 15 min |
| Migration | 5 min |
| Frontend changes | 20 min |
| Testing | 30 min |
| **Total** | ~1 hour |

---

## Dependencies

- Alembic installed and configured
- Database access for migrations
- Backend and frontend dev servers running for testing
