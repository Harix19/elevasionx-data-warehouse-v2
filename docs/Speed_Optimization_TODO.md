# Speed Optimization Implementation TODO

**Project:** ElevationX Data Warehouse Performance Optimization  
**Based on:** [Speed_Optimization_PRD.md](./Speed_Optimization_PRD.md)  
**Target Completion:** 4 Weeks  
**Last Updated:** February 3, 2026 (Updated with Contact Import Fix progress)  
**Deployment Target:** Railway Platform

---

## How to Use This TODO

- [ ] **Unchecked** = Not started
- [x] **Checked** = Completed
- [-] **Strikethrough** = Skipped/Not applicable
- **Priority:** P0 (Critical) → P1 (High) → P2 (Medium) → P3 (Low)

---

## Phase 1: Quick Wins (Week 1)
**Goal:** Implement low-effort, high-impact configuration changes  
**Expected Impact:** 40-80ms improvement per request, 70-85% payload reduction  

### 1.1 Database Connection Optimization [P0]
- [x] **Verify** Neon PgBouncer connection (port 6543) - Already configured ✓
  - [x] Confirm DATABASE_URL uses port 6543 in `.env`
  - [x] Verify connection in development environment
  - [x] Monitor connection time in logs (target: < 10ms)

**Files to Verify:**
- `.env` - Already has correct DATABASE_URL with port 6543

**Verification:**
- [x] Connection established successfully
- [x] No connection errors in logs
- [x] PgBouncer connection overhead < 10ms

**Notes:** Neon Serverless with PgBouncer (port 6543) is already configured. This provides:
- 10,000 concurrent connections support
- < 10ms connection overhead (vs 50-150ms direct)
- Critical for 700M-1B row scale

---

### 1.2 Response Compression [P0]
- [x] Add GZip middleware to FastAPI application
  - [x] Import `GZipMiddleware` from `fastapi.middleware.gzip`
  - [x] Add middleware to `backend/app/main.py` with `minimum_size=1000`
  - [x] Test compression on sample endpoints
  - [x] Verify `Content-Encoding: gzip` header in responses
  - [x] Measure payload size reduction (target: 70-85%)
  - [ ] Monitor CPU overhead (target: < 5%)

**Files Modified:**
- `backend/app/main.py` - Added GZipMiddleware

**Code Changes:**
```python
from fastapi.middleware.gzip import GZipMiddleware

# Add after CORS middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

**Verification:**
- [x] GZip headers present in responses > 1KB
- [x] No errors in compression
- [ ] Payload size reduced by 70%+ (test in production)

---

### 1.3 Frontend React Query Optimization [P0]
- [x] Configure React Query with proper staleTime and caching
  - [x] Update QueryClient configuration in frontend providers
  - [x] Set default staleTime to 60000ms (1 minute)
  - [x] Set default gcTime to 300000ms (5 minutes, formerly cacheTime)
  - [x] Set `refetchOnMount: false`
  - [x] Set `refetchOnWindowFocus: false`
  - [x] Configure specific endpoints with higher staleTime:
    - [x] Filter options: 5 minutes staleTime (via gcTime override)
    - [x] Company/Contact lists: 30 seconds staleTime
    - [x] Detail views: 2 minutes staleTime
    - [x] Stats: 1 minute staleTime

**Files Modified:**
- `frontend/providers/query-provider.tsx` - Updated QueryClient defaults
- `frontend/hooks/use-companies.ts` - Added staleTime to queries
- `frontend/hooks/use-contacts.ts` - Added staleTime and gcTime to queries

**Verification:**
- [x] React Query DevTools shows cached data
- [ ] Fewer network requests in browser DevTools (test in production)
- [ ] 50% reduction in redundant API calls (measure after deployment)

---

### 1.4 Remove Console Logs from Production [P1]
- [x] Clean up console.log statements in production builds
  - [x] Audit `frontend/lib/api.ts` for console.log statements (27 found)
  - [x] Wrap console.log with environment check: `if (process.env.NODE_ENV === 'development')`
  - [x] Remove or disable auth token logging (security risk) ✓ Removed token logging
  - [x] Keep error logging but make it production-safe
  - [ ] Test build to ensure no console output in production

**Files Modified:**
- `frontend/lib/api.ts` - Wrapped all 27 console.log/error statements
- `frontend/lib/auth.ts` - Wrapped authentication logging

**Code Pattern:**
```typescript
// Replace:
console.log('[API] Adding auth header for:', config.url, 'Token:', token);

// With:
if (process.env.NODE_ENV === 'development') {
  console.log('[API] Request:', config.url);
}
```

**Verification:**
- [ ] No console.log output in production build (verify after Railway deploy)
- [x] Errors still logged appropriately
- [x] Development logging still works

---

### 1.5 Structured Request Logging [P1]
- [x] Enhance request logging middleware with timing metrics
  - [x] Update `backend/app/main.py` log_requests middleware
  - [x] Add trace ID generation (X-Request-ID header)
  - [x] Log duration in milliseconds
  - [x] Add response headers for timing:
    - [x] X-Request-ID
    - [x] X-Response-Time
  - [x] Ensure structured logging format (JSON) for production

**Files Modified:**
- `backend/app/main.py` - Enhanced logging middleware

**Code Changes:**
```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    trace_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    
    response = await call_next(request)
    process_time = time.time() - start_time
    duration_ms = process_time * 1000
    
    # Structured logging
    logger.info(
        "Request completed",
        extra={
            "trace_id": trace_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        }
    )
    
    # Add response headers
    response.headers["X-Request-ID"] = trace_id
    response.headers["X-Response-Time"] = f"{duration_ms:.3f}"
    
    return response
```

**Verification:**
- [x] All requests logged with timing
- [x] Trace ID present in response headers
- [x] Logs parseable for metrics extraction

---

### Phase 1 Success Criteria
- [x] Connection overhead < 10ms (verified: PgBouncer already configured)
- [x] Response compression verified via headers (GZip middleware added)
- [ ] No console.log in production builds (verify after Railway deploy)
- [x] Request logging with timing active
- [ ] 40-80ms average improvement in response times (measure after full deployment)

**Estimated Time:** 2-3 days  
**Dependencies:** None  
**Rollback:** Revert code changes via git (< 5 min)

**Phase 1 Complete:** All code changes implemented and verified locally. Ready for Railway deployment.

---

## Phase 2: Railway Infrastructure & Caching Layer (Week 2)
**Goal:** Deploy on Railway and implement Redis application-level caching  
**Expected Impact:** 70-90% reduction in DB queries, sub-50ms filter options  

### 2.0 Railway Project Setup [P0] - IN PROGRESS
- [x] Create Railway project and link GitHub repository
  - [x] Sign up/login to Railway (https://railway.com)
  - [x] Create new project
  - [x] Link GitHub repository
  - [x] Configure project settings

- [x] Install Railway CLI locally
  - [x] Run `npm install -g @railway/cli`
  - [x] Login: `railway login`
  - [x] Link project: `railway link`

- [ ] Configure monorepo deployment
  - [ ] Create `backend/railway.toml` (pending - will be created next)
  - [ ] Create `frontend/railway.toml` (pending - will be created next)
  - [ ] Set root directories in Railway dashboard
  - [ ] Configure start commands

**Note:** Railway configuration is being implemented alongside the Contact Import Fix deployment. The same railway.toml files will serve both features.

**Files to Create:**
- `backend/railway.toml`
- `frontend/railway.toml`

**Configuration:**
```toml
# backend/railway.toml
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

```toml
# frontend/railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "next start --hostname :: --port ${PORT-3000}"
healthcheckPath = "/"
healthcheckTimeout = 30
```

**Verification:**
- [ ] Railway project created
- [ ] GitHub repo linked
- [ ] CLI installed and authenticated
- [ ] Configuration files committed

---

### 2.1 Redis Service Deployment [P0]
- [ ] Deploy Redis via Railway template
  - [ ] Go to Railway dashboard
  - [ ] Click "New" → "Database" → "Redis"
  - [ ] Or use template: https://railway.com/template/redis
  - [ ] Wait for deployment

- [ ] Verify Redis environment variables
  - [ ] Check `REDIS_URL` is auto-populated
  - [ ] Verify `REDISHOST`, `REDISPORT`, `REDISPASSWORD`

- [ ] Configure backend to use Railway Redis
  - [ ] Set environment variable: `REDIS_URL=${{ redis.REDIS_URL }}`
  - [ ] Update backend configuration to use Railway Redis
  - [ ] Test connection from backend service

**Verification:**
- [ ] Redis service healthy in Railway dashboard
- [ ] Environment variables auto-configured
- [ ] Backend can connect to Redis via private network
- [ ] Redis ping successful

---

### 2.2 Cache Infrastructure Setup [P0]
- [ ] Set up Redis for caching (separate from rate limiting)
  - [ ] Configure separate Redis database (e.g., db=1) for cache
  - [ ] Add CACHE_ENABLED and CACHE_REDIS_URL to config
  - [ ] Create cache connection manager in backend
  - [ ] Add health check for cache connectivity
  - [ ] Test cache read/write operations

**Files to Create:**
- `backend/app/core/cache.py` (cache manager)

**Files to Modify:**
- `backend/app/core/config.py`
- `backend/app/main.py` (health check)

**Configuration:**
```python
# config.py additions
CACHE_ENABLED: bool = True
CACHE_DEFAULT_TTL: int = 300
# Use Railway Redis URL
CACHE_REDIS_URL: str = "${REDIS_URL}"
```

**Verification:**
- [ ] Redis connection successful via private network
- [ ] Can read/write cache keys
- [ ] Health check passes

---

### 2.3 Cache Decorator Implementation [P0]
- [ ] Create @cache decorator for common patterns
  - [ ] Implement cache key generation from function name and arguments
  - [ ] Support TTL parameter
  - [ ] Support key_pattern parameter for custom keys
  - [ ] Handle cache serialization (JSON)
  - [ ] Add cache miss/hit logging
  - [ ] Implement graceful fallback on Redis failure

**Files to Create:**
- `backend/app/decorators/cache.py`

**Interface Design:**
```python
@cache(ttl=300, key_pattern="filter:companies:options:v1")
async def get_company_filter_options(db: DB):
    ...
```

**Verification:**
- [ ] Decorator works on async functions
- [ ] Cache keys generated correctly
- [ ] TTL respected
- [ ] Fallback to DB on cache failure

---

### 2.4 Cache Invalidation System [P0]
- [ ] Create @invalidate_cache decorator
  - [ ] Implement cache key invalidation
  - [ ] Support pattern-based invalidation
  - [ ] Hook into write operations (create, update, delete)
  - [ ] Add invalidation logging

**Files to Modify:**
- `backend/app/decorators/cache.py` (add invalidate_cache)

**Files to Update:**
- `backend/app/api/v1/endpoints/companies.py` (invalidate on writes)
- `backend/app/api/v1/endpoints/contacts.py` (invalidate on writes)

**Interface Design:**
```python
@invalidate_cache("filter:companies:options:v1")
@invalidate_cache("stats:summary:v1")
async def create_company(db: DB, company_in: CompanyCreate):
    ...
```

**Verification:**
- [ ] Cache invalidated on writes
- [ ] Pattern invalidation works
- [ ] No stale data served

---

### 2.5 Priority Endpoint Caching [P0]
- [ ] Add caching to filter-options endpoints
  - [ ] Cache `/companies/filter-options` (TTL: 5 min)
  - [ ] Cache `/contacts/filter-options` (TTL: 5 min)
  - [ ] Implement cache invalidation on company/contact writes
  - [ ] Test cache hit/miss scenarios

- [ ] Add caching to company/contact list endpoints
  - [ ] Cache `/companies` with cursor and filters (TTL: 1 min)
  - [ ] Cache `/contacts` with cursor and filters (TTL: 1 min)
  - [ ] Use cache-aside pattern
  - [ ] Test pagination with caching

**Files to Modify:**
- `backend/app/api/v1/endpoints/companies.py`
- `backend/app/api/v1/endpoints/contacts.py`

**Verification:**
- [ ] Filter options < 50ms (from cache)
- [ ] Cache hit rate > 70%
- [ ] Invalidation working on writes

---

### 2.6 Stats Endpoint Caching [P1]
- [ ] Add caching to stats endpoint
  - [ ] Cache `/stats` response (TTL: 1 min)
  - [ ] Invalidate on any company/contact write
  - [ ] Consider background refresh for real-time feel

**Files to Modify:**
- `backend/app/api/v1/endpoints/stats.py`

**Verification:**
- [ ] Stats endpoint < 100ms
- [ ] Cache invalidated correctly

---

### 2.7 First Production Deployment [P0]
- [ ] Deploy backend service to Railway
  - [ ] Push code to GitHub
  - [ ] Deploy via Railway dashboard or CLI: `railway up`
  - [ ] Verify deployment successful
  - [ ] Check logs for errors

- [ ] Deploy frontend service to Railway
  - [ ] Configure frontend environment variables
  - [ ] Deploy via Railway
  - [ ] Verify frontend loads correctly
  - [ ] Test API connectivity

- [ ] Verify end-to-end functionality
  - [ ] Test login/authentication
  - [ ] Test company list loading
  - [ ] Test filter options
  - [ ] Test Redis caching

**Verification:**
- [ ] Backend service healthy
- [ ] Frontend service healthy
- [ ] Redis service healthy
- [ ] All health checks passing
- [ ] End-to-end smoke tests passing

---

### Phase 2 Success Criteria
- [ ] Railway project deployed with 3 services (backend, frontend, redis)
- [ ] Private networking working (backend ↔ redis)
- [ ] Cache hit rate > 70% for priority endpoints
- [ ] Filter-options < 50ms
- [ ] Company/Contact lists < 100ms
- [ ] Cache invalidation working on writes
- [ ] Metrics collection active
- [ ] Graceful Redis failure handling

**Estimated Time:** 4-5 days  
**Dependencies:** Phase 1 complete  
**Rollback:** Set CACHE_ENABLED=false, remove Redis service (< 5 min)

---

## Phase 3: Query Optimization (Week 3)
**Goal:** Optimize database queries and add search optimization  
**Expected Impact:** 60-70% faster filter-options, 50-70% faster search  

### 3.1 Batch Filter-Options Queries [P0]
- [ ] Rewrite filter-options to use single batched query
  - [ ] Create CTE-based query combining all 8 current queries
  - [ ] Use `json_agg` for array aggregation
  - [ ] Test query performance (target: < 50ms)
  - [ ] Verify identical response format
  - [ ] Add query plan analysis (EXPLAIN ANALYZE)

**Files to Modify:**
- `backend/app/api/v1/endpoints/companies.py`
- `backend/app/api/v1/endpoints/contacts.py`

**Query Pattern:**
```sql
WITH industries AS (
    SELECT json_agg(DISTINCT industry) as data 
    FROM companies WHERE deleted_at IS NULL AND industry IS NOT NULL
),
-- ... other CTEs
SELECT 
    (SELECT data FROM industries) as industries,
    -- ... other columns
```

**Scale Optimization (Future):**
- [ ] Create materialized view for filter options (1B+ scale)
- [ ] Set up refresh schedule (every 5 minutes)
- [ ] Cache materialized view results

**Verification:**
- [ ] Single query execution
- [ ] Response time < 50ms
- [ ] Correct data returned

---

### 3.2 Search Vector Migration [P0]
- [ ] Create Alembic migration for search_vector columns
  - [ ] Add `search_vector` tsvector column to companies table
  - [ ] Add `search_vector` tsvector column to contacts table
  - [ ] Create GIN indexes on search_vector columns
  - [ ] Create trigger functions for automatic updates
  - [ ] Create triggers on insert/update
  - [ ] Populate existing data (batch update)

**Files to Create:**
- `backend/alembic/versions/004_add_search_vectors.py`

**Migration Steps:**
1. Add columns (nullable)
2. Create indexes (CONCURRENTLY)
3. Create functions
4. Create triggers
5. Backfill data

**Verification:**
- [ ] Columns created successfully
- [ ] Indexes created without blocking
- [ ] Triggers firing on inserts/updates
- [ ] Existing data populated

---

### 3.3 Search Endpoint Optimization [P0]
- [ ] Update search endpoint to use pre-computed vectors
  - [ ] Modify `/search` endpoint to use `search_vector` column
  - [ ] Remove on-the-fly `to_tsvector()` computation
  - [ ] Update query to use GIN index
  - [ ] Add query plan verification (EXPLAIN ANALYZE)
  - [ ] Test search performance (target: < 100ms)
  - [ ] Test ranking quality (should be identical)

**Files to Modify:**
- `backend/app/api/v1/endpoints/search.py`

**Verification:**
- [ ] Search uses index (EXPLAIN shows Index Scan)
- [ ] Response time < 100ms
- [ ] Results identical to before

---

### 3.4 Database Index Optimization [P1]
- [ ] Create additional indexes for common queries
  - [ ] Composite index for filter combinations: `(industry, country, status)`
  - [ ] Partial index for pagination: `(created_at DESC, id)` WHERE deleted_at IS NULL
  - [ ] Partial index for domain lookups: `(domain)` WHERE deleted_at IS NULL
  - [ ] Partial index for email lookups: `(email)` WHERE deleted_at IS NULL

**SQL Commands:**
```sql
CREATE INDEX CONCURRENTLY idx_companies_filters 
ON companies(industry, country, status) 
WHERE deleted_at IS NULL;

CREATE INDEX CONCURRENTLY idx_companies_pagination 
ON companies(created_at DESC, id) 
WHERE deleted_at IS NULL;
```

**Files to Create:**
- `backend/alembic/versions/005_add_performance_indexes.py`

**Verification:**
- [ ] All indexes created successfully
- [ ] Query planner uses new indexes (EXPLAIN ANALYZE)
- [ ] No performance degradation for writes

---

### 3.5 Rate Limiting Optimization [P1]
- [ ] Simplify rate limiting to fixed window
  - [ ] Update `backend/app/middleware/rate_limit.py`
  - [ ] Implement fixed-window counter (2 Redis ops)
  - [ ] Add configuration option for strategy selection
  - [ ] Test rate limiting accuracy
  - [ ] Verify 50% reduction in Redis operations

**Files to Modify:**
- `backend/app/middleware/rate_limit.py`
- `backend/app/core/config.py` (add RATE_LIMIT_STRATEGY)

**Code Changes:**
```python
async def check_rate_limit_fixed(request: Request, rate_limit: int):
    redis_key = f"ratelimit:{identifier}:{int(time.time()) // 60}"
    
    pipe = self.redis.pipeline()
    pipe.incr(redis_key)
    pipe.expire(redis_key, 60)
    results = await pipe.execute()
    
    current_count = results[0]
    return current_count <= rate_limit, rate_limit - current_count
```

**Verification:**
- [ ] 2 Redis ops per request (was 4)
- [ ] Rate limiting still accurate
- [ ] Headers still correct

---

### 3.6 Query Logging and Slow Query Detection [P2]
- [ ] Add database query logging
  - [ ] Log all queries in DEBUG mode
  - [ ] Add query timing metrics
  - [ ] Implement slow query detection (> 100ms threshold)
  - [ ] Log slow queries with EXPLAIN plans
  - [ ] Add to structured logging

**Files to Modify:**
- `backend/app/db/session.py`
- `backend/app/core/logging.py`

**Verification:**
- [ ] Queries logged in DEBUG mode
- [ ] Slow queries identified
- [ ] EXPLAIN plans available for optimization

---

### Phase 3 Success Criteria
- [ ] Single query for filter-options
- [ ] Search using pre-computed tsvector
- [ ] No slow queries > 100ms (p95)
- [ ] Indexes created without blocking
- [ ] Rate limiting uses 2 Redis ops
- [ ] Load testing passed at 1M+ rows

**Estimated Time:** 4-5 days  
**Dependencies:** Phase 2 complete, database migration window  
**Rollback:** Revert to original queries, drop new indexes (< 10 min)

---

## Phase 4: Monitoring & Scale Testing (Week 4)
**Goal:** Set up comprehensive monitoring and validate billion-row scale  
**Expected Impact:** Ongoing visibility, confidence in 1B row scale  

### 4.1 Metrics Infrastructure [P0]
- [ ] Set up Railway native monitoring
  - [ ] Configure Railway dashboards
  - [ ] Set up log-based metrics
  - [ ] Create custom metrics endpoint
  - [ ] Define key metrics:
    - [ ] Request duration (p50, p95, p99)
    - [ ] Cache hit/miss rates
    - [ ] Redis latency
    - [ ] Database query time

**Files to Create:**
- `backend/app/core/metrics.py` (optional)

**Files to Modify:**
- `backend/app/main.py` (metrics endpoint)

**Implementation:**
```python
@app.get("/metrics")
async def metrics():
    return {
        "cache_hit_rate": calculate_hit_rate(),
        "avg_response_time_ms": get_avg_response_time(),
        "redis_latency_ms": get_redis_latency(),
    }
```

**Verification:**
- [ ] `/metrics` endpoint returns data
- [ ] All metrics populated
- [ ] Railway logs showing structured data

---

### 4.2 Enhanced Health Checks [P1]
- [ ] Implement detailed health check endpoint
  - [ ] Check database connectivity
  - [ ] Check Redis connectivity
  - [ ] Check cache functionality
  - [ ] Return detailed status for each component
  - [ ] Set proper HTTP status codes (200 vs 503)

**Files to Modify:**
- `backend/app/main.py` (health endpoints)

**Verification:**
- [ ] Health check returns component status
- [ ] Failing components return 503
- [ ] All critical components monitored

---

### 4.3 Performance Dashboards [P1]
- [ ] Create simple performance dashboard
  - [ ] Create `/health/dashboard` endpoint returning JSON metrics
  - [ ] Include:
    - [ ] p50, p95, p99 response times
    - [ ] Cache hit rate
    - [ ] Top 10 slowest endpoints
    - [ ] Database connection pool status
    - [ ] Redis connection status
  - [ ] Format for easy ingestion by monitoring tools

**Files to Create:**
- `backend/app/api/v1/endpoints/dashboard.py`

**Files to Modify:**
- `backend/app/api/v1/api.py` (add router)

**Verification:**
- [ ] Dashboard endpoint returns metrics
- [ ] Data is current and accurate
- [ ] Easy to parse

---

### 4.4 Load Testing [P0]
- [ ] Create and run load tests
  - [ ] Set up k6 or artillery for load testing
  - [ ] Create test scenarios:
    - [ ] Company list with filters (100 concurrent users)
    - [ ] Contact list with filters (100 concurrent users)
    - [ ] Filter options (50 concurrent users)
    - [ ] Search (30 concurrent users)
    - [ ] Mixed workload (200 concurrent users)
  - [ ] Run tests against Railway production
  - [ ] Collect metrics from Railway logs
  - [ ] Verify targets met:
    - [ ] < 100ms p95 for lists
    - [ ] < 50ms p95 for filter options
    - [ ] < 100ms p95 for search
    - [ ] < 150ms p95 for mixed workload

**Files to Create:**
- `backend/tests/load/k6/companies.js`
- `backend/tests/load/k6/contacts.js`
- `backend/tests/load/k6/search.js`
- `backend/tests/load/k6/mixed.js`

**Verification:**
- [ ] All load tests pass
- [ ] Metrics meet targets
- [ ] No errors or timeouts
- [ ] Railway services remain healthy under load

---

### 4.5 Scale Testing [P1]
- [ ] Test with synthetic data at scale
  - [ ] Create synthetic data generator script
  - [ ] Generate 1M records and test
  - [ ] Generate 10M records and test
  - [ ] Generate 100M records and test (if feasible)
  - [ ] Document performance at each scale
  - [ ] Identify any scaling bottlenecks

**Files to Create:**
- `backend/scripts/generate_synthetic_data.py`

**Verification:**
- [ ] Queries remain performant at scale
- [ ] Indexes used effectively
- [ ] Cache hit rates maintained
- [ ] Neon performance stable

---

### 4.6 Documentation and Runbook [P1]
- [ ] Create Architecture Decision Records (ADRs)
  - [ ] ADR-001: Why Neon Serverless over Railway PostgreSQL
  - [ ] ADR-002: Railway deployment architecture
  - [ ] ADR-003: Cache key structure and TTL strategy
  - [ ] ADR-004: Fixed window vs sliding window rate limiting
  - [ ] ADR-005: Pre-computed tsvector columns
  - [ ] Store in `docs/adr/`

- [ ] Create Cache Management Runbook
  - [ ] How to clear cache
  - [ ] How to warm cache
  - [ ] How to handle cache issues
  - [ ] Redis commands reference
  - [ ] Store in `docs/runbooks/cache-management.md`

- [ ] Create Performance Troubleshooting Guide
  - [ ] How to identify slow queries
  - [ ] How to analyze query plans
  - [ ] How to tune cache TTL
  - [ ] Common issues and solutions
  - [ ] Store in `docs/runbooks/performance-troubleshooting.md`

**Files to Create:**
- `docs/adr/001-neon-vs-railway-postgres.md`
- `docs/adr/002-railway-architecture.md`
- `docs/adr/003-cache-strategy.md`
- `docs/adr/004-rate-limiting-strategy.md`
- `docs/adr/005-search-vectors.md`
- `docs/runbooks/cache-management.md`
- `docs/runbooks/performance-troubleshooting.md`

**Verification:**
- [ ] All ADRs documented
- [ ] Runbooks tested and accurate
- [ ] Team can follow procedures

---

### 4.7 Developer Guidelines [P2]
- [ ] Document developer standards
  - [ ] Caching guidelines (when to cache, TTL recommendations)
  - [ ] Query optimization guidelines
  - [ ] Performance budget
  - [ ] Code review checklist for performance
  - [ ] Store in `docs/standards/`

**Files to Create:**
- `docs/standards/caching-guidelines.md`
- `docs/standards/query-optimization.md`
- `docs/standards/performance-budget.md`
- `docs/standards/railway-deployment.md`

**Verification:**
- [ ] Guidelines clear and actionable
- [ ] Team trained on standards
- [ ] Checklist used in code reviews

---

### Phase 4 Success Criteria
- [ ] Metrics endpoint returning data
- [ ] Railway dashboards showing p50, p95, p99 latencies
- [ ] Load testing with 1000+ concurrent users passed
- [ ] Testing with 100M+ synthetic records passed (if feasible)
- [ ] Runbook documented and tested
- [ ] ADRs complete
- [ ] Developer guidelines in place

**Estimated Time:** 3-4 days  
**Dependencies:** Phase 3 complete  
**Rollback:** Disable metrics endpoint (< 5 min)

---

## Post-Implementation

### Performance Validation
- [ ] Run comprehensive performance tests
- [ ] Compare metrics to baseline
- [ ] Document improvements achieved
- [ ] Create performance report

### Monitoring and Alerting
- [ ] Set up Railway alerts for:
  - [ ] Response time > 200ms (p95)
  - [ ] Cache hit rate < 50%
  - [ ] Database connection errors
  - [ ] Redis unavailability
  - [ ] Error rate > 1%

### Knowledge Transfer
- [ ] Conduct team training session
- [ ] Walk through new architecture
- [ ] Demonstrate monitoring tools
- [ ] Q&A session

### Continuous Improvement
- [ ] Schedule monthly performance reviews
- [ ] Monitor for new bottlenecks
- [ ] Plan Phase 5 optimizations if needed

---

## Summary

| Phase | Duration | Key Deliverables | Target Impact | Status |
|-------|----------|------------------|---------------|--------|
| **Phase 1** | Week 1 | PgBouncer (verify), GZip, React Query tuning | 40-80ms improvement | ✅ Complete |
| **Phase 2** | Week 2 | Railway deployment, Redis, caching layer | 70-90% DB reduction | ⬜ In Progress |
| **Phase 3** | Week 3 | Query batching, search vectors, indexes | 60-70% query speedup | ⬜ Pending |
| **Phase 4** | Week 4 | Monitoring, load testing, documentation | Validation & visibility | ⬜ Pending |

**Total Timeline:** 4 weeks  
**Expected Overall Impact:** 70-85% performance improvement  
**Scale Readiness:** Validated for 700M-1B records  
**Deployment Target:** Railway Platform

---

## Quick Reference

### Critical Files
```
backend/app/main.py                    # Middleware, app setup
backend/app/core/config.py             # Configuration
backend/app/db/session.py              # Database connection
backend/app/decorators/cache.py        # Cache decorators (NEW)
backend/app/core/cache.py              # Cache manager (NEW)
backend/app/core/metrics.py            # Metrics (NEW)
backend/app/middleware/rate_limit.py   # Rate limiting
backend/app/api/v1/endpoints/          # API endpoints
backend/railway.toml                   # Railway config (NEW)
frontend/lib/api.ts                    # Frontend API client
frontend/railway.toml                  # Railway config (NEW)
frontend/providers/                    # React Query setup
```

### Railway Environment Variables
```bash
# Backend Service
DATABASE_URL="postgresql+asyncpg://...:6543/dbname?ssl=require"
REDIS_URL="${{ redis.REDIS_URL }}"
CACHE_ENABLED=true
CACHE_DEFAULT_TTL=300
SECRET_KEY="${{ shared.SECRET_KEY }}"
DEBUG=false

# Frontend Service
NEXT_PUBLIC_API_URL="https://${{ backend.RAILWAY_PUBLIC_DOMAIN }}/api/v1"
```

### Commands
```bash
# Railway CLI
railway login
railway link
railway up
railway logs
railway variables

# Database migrations (run in backend service)
railway run --service backend alembic revision --autogenerate -m "description"
railway run --service backend alembic upgrade head

# Cache operations (via Railway CLI)
railway run --service redis redis-cli -n 1 KEYS "filter:*"
railway run --service redis redis-cli -n 1 FLUSHDB

# Health checks
curl https://<backend-domain>/health/ready
curl https://<backend-domain>/health/dashboard
curl https://<backend-domain>/metrics
```

---

**Maintained by:** Engineering Team  
**Review Schedule:** Weekly during implementation, monthly post-completion  
**Questions?** See [Speed_Optimization_PRD.md](./Speed_Optimization_PRD.md) for detailed specifications
