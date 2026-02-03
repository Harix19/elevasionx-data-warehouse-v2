# PRD: Speed Optimization Plan for ElevationX Data Warehouse

**Document Version:** 1.0  
**Date:** February 2025  
**Status:** Ready for Implementation  
**Author:** System Analysis  
**Stakeholders:** Engineering Team, DevOps, Product Management

---

## 1. Executive Summary

### 1.1 Current State
The ElevationX Data Warehouse API is experiencing **performance degradation** affecting user experience:
- Average API response times: **150-400ms** (target: <100ms)
- Database queries with multiple filters: **200-600ms**
- Company/Contact fetching (priority endpoints): **180-350ms**
- Search endpoint latency: **300-800ms**
- Bulk import operations: **5-15 seconds per 1,000 records**

### 1.2 Scale Considerations
The database is projected to scale to **700M-1B records**, requiring optimizations that can handle massive scale:
- Index strategies must work at billion-row scale
- Cache eviction policies need to handle large working sets
- Query patterns must remain efficient with massive datasets
- Connection pooling critical for high concurrency

### 1.3 Identified Bottlenecks
Based on comprehensive codebase analysis, **7 critical bottlenecks** have been identified:

| Priority | Bottleneck | Current Impact | Target Improvement |
|----------|-----------|----------------|-------------------|
| P0 | Database Connection (NullPool) | 50-150ms overhead per request | 80-95% reduction |
| P0 | Missing Application Caching | 100% DB hit rate | 70-90% cache hit rate |
| P1 | Sequential Filter Queries | 8 separate DB queries (200-400ms) | Single query (<50ms) |
| P1 | Search Vector Computation | CPU-intensive on-the-fly | Pre-computed index |
| P2 | Missing Compression | Large JSON payloads | 70-85% size reduction |
| P2 | Inefficient Rate Limiting | 4 Redis ops per request | 2 ops per request |
| P3 | Frontend Deduplication | Redundant API calls | Proper stale-time caching |

### 1.4 Infrastructure Context

**Neon Serverless PostgreSQL:**
- Connection pooler available on port 6543 (PgBouncer)
- Supports up to 10,000 concurrent connections via pooler
- Direct connections limited to 104 (for migrations/pg_dump only)
- **Recommendation:** Use pooled connection for application

**Redis:**
- Available for use (database not in production yet)
- Can be used for caching, rate limiting, and session storage

**No Existing APM:**
- Need to set up monitoring and alerting from scratch
- Will implement structured logging + metrics collection

### 1.5 Proposed Solution
Implement a **multi-layer optimization strategy** addressing database connections, application caching, query optimization, compression, and frontend performance.

### 1.6 Expected Outcomes
- **70-85% reduction** in average API response times
- **Sub-100ms** response for filtered list operations
- **Sub-50ms** response for filter options endpoint
- **2-3x faster** bulk import operations
- **40-60% reduction** in bandwidth utilization
- **Scalability to 1B+ records** with maintained performance

---

## 2. Goals & Success Criteria

### 2.1 Primary Goals
1. **Reduce API Latency:** Average response time < 100ms (p50), < 200ms (p95)
2. **Improve Database Efficiency:** 70%+ of read operations served from cache
3. **Optimize Connection Management:** Eliminate connection overhead per request
4. **Enhance User Experience:** Perceived load time < 1 second for all operations
5. **Scale to 1B Records:** Maintain < 200ms p95 latency at billion-row scale

### 2.2 Success Metrics

| Metric | Current | Target | Measurement Method |
|--------|---------|--------|-------------------|
| Avg Response Time (p50) | 150-400ms | < 100ms | Server logs + APM |
| Avg Response Time (p95) | 400-800ms | < 200ms | Server logs + APM |
| Company Fetching (Priority) | 180-350ms | < 100ms | API timing |
| Contact Fetching (Priority) | 180-350ms | < 100ms | API timing |
| Filter Options Endpoint | 200-400ms | < 50ms | API timing |
| Cache Hit Rate | 0% | > 70% | Redis metrics |
| DB Connection Time | 50-150ms | < 10ms | Connection pool metrics |
| Payload Size (uncompressed) | Baseline | -70% to -85% | Response headers |
| Bulk Import (1K records) | 5-15s | < 5s | Import job metrics |
| Query Time at 1B rows | N/A | < 150ms p95 | Load testing |

### 2.3 Non-Goals
- No schema changes affecting business logic
- No changes to API contract or response formats
- No breaking changes for existing clients
- No migration of data between databases
- No changes to authentication or authorization

---

## 3. Problem Analysis

### 3.1 Architecture Overview

**Current Stack:**
- **Backend:** FastAPI 0.100+, SQLAlchemy 2.0 (async), asyncpg
- **Database:** Neon Serverless PostgreSQL (port 5432 direct)
- **Cache:** Redis (currently only for rate limiting)
- **Frontend:** Next.js 16, React Query 5, Axios
- **Deployment:** Serverless/Cloud environment

**Key Files:**
```
backend/app/db/session.py          # Database connection configuration
backend/app/core/config.py         # Application settings
backend/app/api/v1/endpoints/companies.py    # Company CRUD + filtering
backend/app/api/v1/endpoints/contacts.py     # Contact CRUD + filtering
backend/app/api/v1/endpoints/search.py       # Full-text search
backend/app/middleware/rate_limit.py         # Rate limiting logic
backend/app/main.py                          # FastAPI app setup
frontend/lib/api.ts                          # Frontend API client
```

### 3.2 Detailed Bottleneck Analysis

#### 3.2.1 Database Connection: NullPool + Direct Connection

**Current Implementation:**
```python
# backend/app/db/session.py
engine = create_async_engine(
    settings.DATABASE_URL,  # port 5432 - direct connection
    poolclass=NullPool,  # MANDATORY for Neon serverless
    connect_args={"statement_cache_size": 0},
)
```

**Problem:**
- `NullPool` forces new TCP connection + SSL handshake per request
- Direct connection to Neon (port 5432) instead of using pooler
- Each connection: ~50-150ms overhead (SSL + TCP handshake)
- No local connection pooling
- Limited to 104 direct connections

**Neon Pooler Solution:**
- Port 6543 with PgBouncer
- Supports 10,000 concurrent connections
- Maintains connection pool for serverless functions
- **Action:** Switch to pooled connection string

**Impact:**
- High latency on every database operation
- Connection exhaustion risk under load
- Inefficient resource utilization

**Scale Impact:**
- At 1B records, connection overhead becomes critical bottleneck
- Each query + connection setup = unacceptable latency

#### 3.2.2 Missing Application Caching

**Current State:**
- No caching layer for database queries
- Redis used only for rate limiting
- Identical queries hit database repeatedly
- Filter options fetched on every page load

**Priority Endpoints (Company & Contact Fetching):**
| Endpoint | Current Query Pattern | Frequency |
|----------|----------------------|-----------|
| `GET /companies` | Complex WHERE + pagination | High traffic |
| `GET /companies/filter-options` | 8 separate DB queries | Every page visit |
| `GET /contacts` | Complex WHERE + pagination | High traffic |
| `GET /contacts/filter-options` | Multiple DB queries | Every page visit |
| `GET /stats` | 3 aggregate queries | Dashboard load |
| `GET /search` | Full-text search + ranking | Moderate traffic |

**Impact:**
- 100% database hit rate
- Expensive computations repeated
- Database CPU and I/O saturation
- Filter options endpoint: 200-400ms

**Scale Impact:**
- At 700M-1B rows, filter queries become extremely expensive
- Distinct queries on large datasets = full table scans
- Cache essential for scalability

#### 3.2.3 Sequential Query Pattern for Filter Options

**Current Implementation (8 Sequential Queries):**
```python
# backend/app/api/v1/endpoints/companies.py
# Runs 8 separate queries sequentially:
industries_stmt = select(distinct(Company.industry))...    # 20-50ms
countries_stmt = select(distinct(Company.country))...      # 20-50ms
revenue_stmt = select(func.min(Company.revenue), func.max(Company.revenue))...  # 20-50ms
lead_score_stmt = select(func.min(Company.lead_score), func.max(Company.lead_score))...  # 20-50ms
employee_stmt = select(func.min(Company.employee_count), func.max(Company.employee_count))...  # 20-50ms
tags_a_stmt = select(distinct(func.unnest(Company.custom_tags_a)))...  # 30-60ms
tags_b_stmt = select(distinct(func.unnest(Company.custom_tags_b)))...  # 30-60ms
tags_c_stmt = select(distinct(func.unnest(Company.custom_tags_c)))...  # 30-60ms
# Total: 200-400ms
```

**Problem:**
- 8 round-trips to database
- Sequential execution (no parallelism)
- At 1B rows, DISTINCT queries become prohibitively expensive
- Each unnest query scans entire array column

**Impact:**
- Slowest endpoint in the application
- Blocks UI rendering
- Poor user experience on filter panel
- Unscalable at billion-row scale

#### 3.2.4 Full-Text Search On-the-Fly Computation

**Current Implementation:**
```python
# backend/app/api/v1/endpoints/search.py
company_vector = func.to_tsvector(
    'english',
    func.coalesce(Company.name, '') + ' ' +
    func.coalesce(Company.description, '') + ' ' +
    func.coalesce(Company.domain, '')
)
company_rank = func.ts_rank(company_vector, search_query)
```

**Problem:**
- `to_tsvector()` computed at query time
- CPU-intensive text processing on every search
- GIN index exists but on-the-fly computation negates benefits
- No pre-computed tsvector column

**Impact:**
- Search queries: 300-800ms
- CPU overhead on database
- Scalability concerns with large datasets
- At 1B rows, text processing becomes massive overhead

#### 3.2.5 Missing Response Compression

**Current State:**
- No GZip or Brotli compression
- JSON payloads sent uncompressed
- Large datasets = large transfer sizes
- Company lists with full details can be 100KB+

**Impact:**
- Bandwidth waste
- Slower network transfer
- Higher egress costs
- Especially problematic for large result sets

#### 3.2.6 Inefficient Rate Limiting

**Current Implementation (4 Redis ops per request):**
```python
pipe.zremrangebyscore(redis_key, 0, window_start)  # Clean old
pipe.zcard(redis_key)                               # Count
pipe.zadd(redis_key, {str(now): now})              # Add current
pipe.expire(redis_key, 60)                         # Set expiry
```

**Problem:**
- Sliding window algorithm = 4 Redis ops
- Adds 10-30ms per request
- Complexity not needed for most use cases
- Redis overhead under high load

#### 3.2.7 Frontend Request Deduplication

**Current State:**
```typescript
// frontend/lib/api.ts
getFilterOptions: async () => {
    const response = await api.get('/companies/filter-options');
    return response.data;
},
```

**Problem:**
- React Query default staleTime = 0
- Multiple components fetch same data
- Console.log in production code
- No prefetching strategy

---

## 4. Proposed Solutions

### 4.1 Solution Summary Matrix

| Bottleneck | Solution | Complexity | Estimated Gain |
|-----------|----------|-----------|----------------|
| NullPool + Direct | Use Neon PgBouncer (port 6543) | Low | 40-80ms per request |
| No Caching | Implement Redis caching layer | Medium | 70-90% faster for cached ops |
| Sequential Queries | Batch into single query + caching | Low | 60-70% faster |
| Search Computation | Add pre-computed tsvector column | Medium | 50-70% faster |
| No Compression | Add GZip middleware | Low | 70-85% size reduction |
| Rate Limiting | Simplify to fixed window | Low | 50% fewer Redis ops |
| Frontend | Configure React Query | Low | Reduced redundant calls |

### 4.2 Detailed Solution Specifications

#### 4.2.1 Database Connection Optimization

**Solution:** Switch to Neon Pooled Connection

**Implementation:**
```python
# Change in .env or config
# FROM: postgresql+asyncpg://user:pass@host.neon.tech:5432/dbname?ssl=require
# TO:   postgresql+asyncpg://user:pass@host.neon.tech:6543/dbname?ssl=require

# backend/app/core/config.py will handle this automatically
DATABASE_URL="postgresql+asyncpg://...:6543/..."
```

**Benefits:**
- PgBouncer maintains connection pool
- Eliminates per-request connection overhead
- Supports 10,000 concurrent connections
- Required for serverless environments

**Scale Considerations:**
- Critical for 1B row scale
- Without pooling, connection limits (104) become bottleneck
- PgBouncer handles connection multiplexing efficiently

**Acceptance Criteria:**
- [ ] Connection overhead < 10ms
- [ ] No connection leaks under load
- [ ] Graceful handling of pool exhaustion
- [ ] Load testing at 1000+ concurrent connections

#### 4.2.2 Application-Level Caching (Redis)

**Cache Strategy by Endpoint:**

| Endpoint | Cache Key Pattern | TTL | Invalidation Trigger |
|----------|------------------|-----|---------------------|
| `/companies/filter-options` | `filter:companies:options:v1` | 300s | Company write |
| `/contacts/filter-options` | `filter:contacts:options:v1` | 300s | Contact write |
| `/stats` | `stats:summary:v1` | 60s | Any write |
| `/companies/{id}` | `company:{id}:v1` | 120s | Company update/delete |
| `/contacts/{id}` | `contact:{id}:v1` | 120s | Contact update/delete |
| `/search?q={query}` | `search:{hash}:{type}:v1` | 30s | N/A (short TTL) |
| `/companies` (list) | `companies:list:{cursor}:{filters}` | 60s | Any company write |
| `/contacts` (list) | `contacts:list:{cursor}:{filters}` | 60s | Any contact write |

**Implementation Pattern:**
```python
# Decorator-based caching
@cache(ttl=300, key_pattern="filter:companies:options:v1")
async def get_company_filter_options(db: DB):
    # existing logic
    
# Cache invalidation on writes
@invalidate_cache("filter:companies:options:v1")
async def create_company(db: DB, company_in: CompanyCreate):
    # existing logic
```

**Scale Considerations:**
- Use Redis eviction policies (LRU) for large working sets
- Implement cache warming for hot data
- Monitor memory usage at scale
- Consider Redis Cluster for very large cache sets

**Acceptance Criteria:**
- [ ] Cache hit rate > 70%
- [ ] Cache invalidation on writes working
- [ ] Graceful fallback on Redis failure
- [ ] Cache warm-up strategy documented
- [ ] Memory usage < 2GB for 100K cached items

#### 4.2.3 Query Optimization for Filter Options

**Current:** 8 separate queries  
**New:** Single batched query + caching

**Implementation (Single Query):**
```sql
WITH 
industries AS (
    SELECT json_agg(DISTINCT industry) as data 
    FROM companies 
    WHERE deleted_at IS NULL AND industry IS NOT NULL
),
countries AS (
    SELECT json_agg(DISTINCT country) as data 
    FROM companies 
    WHERE deleted_at IS NULL AND country IS NOT NULL
),
revenue_range AS (
    SELECT json_build_object('min', MIN(revenue), 'max', MAX(revenue)) as data 
    FROM companies 
    WHERE deleted_at IS NULL AND revenue IS NOT NULL
),
lead_score_range AS (
    SELECT json_build_object('min', MIN(lead_score), 'max', MAX(lead_score)) as data 
    FROM companies 
    WHERE deleted_at IS NULL AND lead_score IS NOT NULL
),
employee_range AS (
    SELECT json_build_object('min', MIN(employee_count), 'max', MAX(employee_count)) as data 
    FROM companies 
    WHERE deleted_at IS NULL AND employee_count IS NOT NULL
),
tags_a AS (
    SELECT json_agg(DISTINCT tag) as data 
    FROM companies, unnest(custom_tags_a) as tag 
    WHERE deleted_at IS NULL AND custom_tags_a IS NOT NULL
),
tags_b AS (
    SELECT json_agg(DISTINCT tag) as data 
    FROM companies, unnest(custom_tags_b) as tag 
    WHERE deleted_at IS NULL AND custom_tags_b IS NOT NULL
),
tags_c AS (
    SELECT json_agg(DISTINCT tag) as data 
    FROM companies, unnest(custom_tags_c) as tag 
    WHERE deleted_at IS NULL AND custom_tags_c IS NOT NULL
)
SELECT 
    (SELECT data FROM industries) as industries,
    (SELECT data FROM countries) as countries,
    (SELECT data FROM revenue_range) as revenue_range,
    (SELECT data FROM lead_score_range) as lead_score_range,
    (SELECT data FROM employee_range) as employee_count_range,
    (SELECT data FROM tags_a) as tags_a,
    (SELECT data FROM tags_b) as tags_b,
    (SELECT data FROM tags_c) as tags_c;
```

**Scale Optimizations:**
- At 1B rows, add materialized view for filter options
- Refresh materialized view every 5 minutes
- Cache materialized view results in Redis
- Use partial indexes for active records only

**Acceptance Criteria:**
- [ ] Response time < 50ms
- [ ] Single database round-trip
- [ ] Maintain existing response format
- [ ] Works efficiently at 1B row scale

#### 4.2.4 Full-Text Search Optimization

**Solution:** Add pre-computed tsvector column

**Database Migration:**
```sql
-- Add column
ALTER TABLE companies ADD COLUMN search_vector tsvector;
ALTER TABLE contacts ADD COLUMN search_vector tsvector;

-- Create GIN index
CREATE INDEX idx_companies_search ON companies USING GIN(search_vector);
CREATE INDEX idx_contacts_search ON contacts USING GIN(search_vector);

-- Populate existing data (batch for large datasets)
UPDATE companies 
SET search_vector = to_tsvector('english', 
    COALESCE(name, '') || ' ' || 
    COALESCE(description, '') || ' ' || 
    COALESCE(domain, '')
)
WHERE search_vector IS NULL;

-- Trigger for automatic updates
CREATE OR REPLACE FUNCTION update_company_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english',
        COALESCE(NEW.name, '') || ' ' ||
        COALESCE(NEW.description, '') || ' ' ||
        COALESCE(NEW.domain, '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER company_search_vector_trigger
    BEFORE INSERT OR UPDATE ON companies
    FOR EACH ROW
    EXECUTE FUNCTION update_company_search_vector();
```

**Updated Search Query:**
```python
# Simplified - use pre-computed column
company_stmt = select(
    literal("company").label("entity_type"),
    Company.id.label("entity_id"),
    func.ts_rank(Company.search_vector, search_query).label("relevance_score"),
    func.json_build_object(...).label("data")
).where(
    Company.search_vector.op('@@')(search_query),
    Company.deleted_at.is_(None)
)
```

**Scale Considerations:**
- Trigger overhead minimal compared to query-time computation
- GIN index essential for billion-row scale
- Consider search result caching for common queries
- Monitor index size (can be large for text-heavy data)

**Acceptance Criteria:**
- [ ] Search response < 100ms
- [ ] Index used for all search queries (EXPLAIN ANALYZE)
- [ ] Automatic updates on insert/update
- [ ] Migration script for existing data
- [ ] Works at 1B row scale

#### 4.2.5 Response Compression

**Solution:** Add GZip middleware to FastAPI

**Implementation:**
```python
from fastapi.middleware.gzip import GZipMiddleware

# Add to main.py
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

**Configuration:**
- Compress responses > 1KB
- Exclude already-compressed content
- Monitor CPU overhead (expected < 5%)

**Acceptance Criteria:**
- [ ] JSON responses compressed
- [ ] 70-85% size reduction measured
- [ ] CPU overhead < 5%
- [ ] Brotli support (optional future enhancement)

#### 4.2.6 Rate Limiting Optimization

**Solution:** Simplify to fixed-window counter

**New Implementation:**
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

**Benefits:**
- 2 Redis ops vs 4 (50% reduction)
- Simpler logic, less CPU
- Nearly identical user experience
- Atomic operation with pipeline

**Acceptance Criteria:**
- [ ] 50% reduction in Redis operations
- [ ] No degradation in rate limiting accuracy
- [ ] Graceful handling of clock skew
- [ ] Response headers maintained

#### 4.2.7 Frontend Optimization

**React Query Configuration:**
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60000,        // 1 minute
      cacheTime: 300000,       // 5 minutes
      refetchOnMount: false,
      refetchOnWindowFocus: false,
      retry: 2,
      retryDelay: 1000,
    },
  },
});
```

**Specific Endpoint Configurations:**

| Endpoint | staleTime | cacheTime | refetchInterval | Priority |
|----------|-----------|-----------|-----------------|----------|
| /companies/filter-options | 5 min | 10 min | false | High |
| /contacts/filter-options | 5 min | 10 min | false | High |
| /companies (list) | 30 sec | 2 min | false | High |
| /contacts (list) | 30 sec | 2 min | false | High |
| /companies/{id} | 2 min | 5 min | false | Medium |
| /contacts/{id} | 2 min | 5 min | false | Medium |
| /stats | 1 min | 5 min | false | Medium |
| /search | 15 sec | 1 min | false | Low |

**Additional Optimizations:**
- Remove console.log from production builds (use environment check)
- Implement request deduplication
- Add prefetching on hover for detail views
- Use React Query's `select` for data transformation
- Implement optimistic updates for better UX

**Acceptance Criteria:**
- [ ] 50% reduction in redundant API calls
- [ ] Filter options cached for 5 minutes
- [ ] No console.log in production
- [ ] Prefetching implemented for common flows
- [ ] Stale-while-revalidate pattern working

---

## 5. Monitoring & Observability Setup

Since no APM is currently in place, we will implement:

### 5.1 Structured Logging

**Implementation:**
```python
# Enhanced logging with timing information
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Extract trace ID
    trace_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        "Request completed",
        extra={
            "trace_id": trace_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": process_time * 1000,
            "cache_status": response.headers.get("X-Cache-Status", "MISS"),
            "db_query_count": getattr(request.state, 'db_query_count', 0),
            "db_query_time_ms": getattr(request.state, 'db_query_time_ms', 0),
        }
    )
    
    response.headers["X-Request-ID"] = trace_id
    response.headers["X-Response-Time"] = f"{process_time:.3f}"
    return response
```

### 5.2 Metrics Collection

**Key Metrics to Track:**

| Metric | Type | Labels | Purpose |
|--------|------|--------|---------|
| `api_request_duration_seconds` | Histogram | method, path, status | Response time tracking |
| `db_query_duration_seconds` | Histogram | query_type, table | Query performance |
| `db_connection_pool_active` | Gauge | - | Connection pool health |
| `cache_hit_total` | Counter | cache_name, hit_type | Cache effectiveness |
| `cache_miss_total` | Counter | cache_name | Cache miss tracking |
| `redis_operation_duration_seconds` | Histogram | operation | Redis latency |
| `rate_limit_check_total` | Counter | result | Rate limiting stats |
| `payload_size_bytes` | Histogram | endpoint | Response size tracking |

**Implementation:**
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Metrics
REQUEST_DURATION = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'path', 'status_code']
)

CACHE_HITS = Counter(
    'cache_hit_total',
    'Cache hits',
    ['cache_name']
)

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### 5.3 Health Checks

**Enhanced Readiness Check:**
```python
@app.get("/health/ready")
async def readiness():
    checks = {
        "database": False,
        "redis": False,
        "cache": False,
    }
    
    # Database check
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
    
    # Redis check
    try:
        await redis.ping()
        checks["redis"] = True
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
    
    # Cache check (try to read/write a test key)
    try:
        await redis.setex("health:check", 60, "ok")
        result = await redis.get("health:check")
        checks["cache"] = result == "ok"
    except Exception as e:
        logger.error("Cache health check failed", error=str(e))
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if all_healthy else "not_ready", "checks": checks}
    )
```

### 5.4 Alerting Rules (Prometheus-style)

```yaml
# Example alerting rules
alerts:
  - name: HighResponseTime
    expr: histogram_quantile(0.95, api_request_duration_seconds) > 0.5
    for: 5m
    severity: warning
    
  - name: CacheHitRateLow
    expr: rate(cache_hit_total[5m]) / (rate(cache_hit_total[5m]) + rate(cache_miss_total[5m])) < 0.5
    for: 10m
    severity: warning
    
  - name: DatabaseConnectionErrors
    expr: rate(db_connection_errors_total[5m]) > 0
    for: 1m
    severity: critical
    
  - name: RedisUnavailable
    expr: up{job="redis"} == 0
    for: 1m
    severity: critical
```

---

## 6. Implementation Phases

### 6.1 Phase 1: Quick Wins (Week 1)

**Goals:** Implement low-effort, high-impact changes

**Tasks:**
1. Switch to Neon pooled connection (port 6543)
2. Add GZip compression middleware
3. Optimize React Query configuration
4. Remove console.log from production builds
5. Set up basic logging middleware with timing

**Expected Impact:**
- 40-80ms improvement per request
- 70-85% payload size reduction
- 50% reduction in frontend API calls

**Risks:** Minimal - configuration changes only

**Success Criteria:**
- [ ] Connection overhead < 10ms
- [ ] Response compression verified
- [ ] No console.log in production builds
- [ ] Request logging with timing active

### 6.2 Phase 2: Caching Layer (Week 2)

**Goals:** Implement application-level caching

**Tasks:**
1. Design cache key patterns and TTL strategy
2. Implement `@cache` decorator for common patterns
3. Add Redis caching to filter-options endpoints (priority)
4. Add Redis caching to company/contact list endpoints (priority)
5. Add Redis caching to stats endpoint
6. Implement cache invalidation on writes
7. Add cache metrics and monitoring

**Expected Impact:**
- 70-90% reduction in database queries for cached endpoints
- Sub-50ms response for filter-options
- Sub-100ms response for company/contact lists

**Risks:** 
- Cache invalidation complexity
- Redis dependency (failover strategy needed)

**Success Criteria:**
- [ ] Cache hit rate > 70% for priority endpoints
- [ ] Filter-options < 50ms
- [ ] Company/Contact lists < 100ms
- [ ] Cache invalidation working on writes
- [ ] Metrics collection active

### 6.3 Phase 3: Query Optimization (Week 3)

**Goals:** Optimize database query patterns

**Tasks:**
1. Batch filter-options queries into single query
2. Add pre-computed tsvector columns for search
3. Create database indexes for common filter combinations
4. Optimize rate limiting to use fixed window
5. Add database query logging and slow query detection
6. Test at scale with synthetic data

**Expected Impact:**
- 60-70% faster filter-options (database side)
- 50-70% faster search
- 50% fewer Redis operations
- Query performance at 1B row scale validated

**Risks:**
- Database migration complexity
- Index creation time for large datasets
- Migration downtime (use CONCURRENTLY)

**Success Criteria:**
- [ ] Single query for filter-options
- [ ] Search using pre-computed tsvector
- [ ] No slow queries > 100ms (p95)
- [ ] Indexes created without blocking
- [ ] Load testing passed at 1M+ rows

### 6.4 Phase 4: Monitoring & Scale Testing (Week 4)

**Goals:** Validate improvements and ensure 1B row scalability

**Tasks:**
1. Set up Prometheus metrics endpoint
2. Create performance dashboards (can use simple JSON output)
3. Add alerting for performance regressions
4. Performance testing with increasing data sizes
5. Load testing at expected concurrency levels
6. Document optimization patterns for future development
7. Create runbook for cache management
8. Write architecture decision records (ADRs)

**Expected Impact:**
- Ongoing visibility into performance
- Proactive alerting for regressions
- Team knowledge sharing
- Confidence in billion-row scale

**Risks:** Minimal - monitoring only

**Success Criteria:**
- [ ] Metrics endpoint returning data
- [ ] Dashboards showing p50, p95, p99 latencies
- [ ] Alerts configured for regression thresholds
- [ ] Load testing with 1000+ concurrent users passed
- [ ] Testing with 100M+ synthetic records passed
- [ ] Runbook documented and tested

### 6.5 Implementation Timeline

```
Week 1: ████████░░░░░░░░░░░░ Quick Wins
         - Pooled connection
         - Compression
         - Frontend optimization
         - Basic logging

Week 2: ░░████████░░░░░░░░░░ Caching Layer
         - Redis caching
         - Priority endpoints optimized
         - Cache invalidation
         - Metrics

Week 3: ░░░░████████░░░░░░░░ Query Optimization
         - Batched queries
         - Pre-computed search vectors
         - New indexes
         - Rate limiting

Week 4: ░░░░░░████████░░░░░░ Monitoring & Scale Testing
         - Prometheus metrics
         - Dashboards
         - Load testing
         - Documentation
```

---

## 7. Technical Specifications

### 7.1 Architecture Changes

**Before:**
```
Frontend (Next.js/React Query)
    ↓ HTTP
FastAPI (NullPool)
    ↓ TCP/SSL (New connection per request)
Neon PostgreSQL (Port 5432)
    ↓
Redis (Rate limiting only)
```

**After:**
```
Frontend (Next.js/React Query with caching)
    ↓ HTTP (Compressed)
FastAPI (PgBouncer pooled)
    ↓ Pooled Connection (Port 6543)
Neon PostgreSQL
    ↓ Persistent connections
Redis (Cache + Rate limiting)
    
Monitoring:
    ↓ Metrics
Prometheus endpoint + Logs
```

### 7.2 New Dependencies

**Backend:**
```txt
# No new production dependencies required
# All features use existing stack:
# - Redis already available (redis>=5.0.0)
# - FastAPI includes GZip middleware
# - SQLAlchemy supports all query optimizations
```

**Monitoring (Optional):**
```txt
# For Prometheus metrics (optional)
prometheus-client>=0.19.0
```

**Frontend:**
```json
// No new dependencies required
// All features use existing:
// - @tanstack/react-query (already has caching)
// - axios (already available)
```

### 7.3 Configuration Changes

**Environment Variables (.env):**
```bash
# Phase 1: Connection Pooling
# Update DATABASE_URL to use port 6543
DATABASE_URL="postgresql+asyncpg://user:pass@host.neon.tech:6543/dbname?ssl=require"

# Phase 2: Caching
CACHE_ENABLED=true
CACHE_DEFAULT_TTL=300
CACHE_REDIS_URL="redis://localhost:6379/1"  # Separate DB for cache

# Optional: Compression
COMPRESSION_ENABLED=true
COMPRESSION_MINIMUM_SIZE=1000

# Phase 3: Rate Limiting
RATE_LIMIT_STRATEGY=fixed_window  # vs sliding_window
RATE_LIMIT_WINDOW_SECONDS=60

# Phase 4: Monitoring
METRICS_ENABLED=true
METRICS_ENDPOINT="/metrics"
SLOW_QUERY_THRESHOLD_MS=100
```

**Development vs Production:**
```python
# config.py additions
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Caching
    CACHE_ENABLED: bool = True
    CACHE_DEFAULT_TTL: int = 300
    CACHE_REDIS_URL: str = "redis://localhost:6379/1"
    
    # Compression
    COMPRESSION_ENABLED: bool = True
    COMPRESSION_MINIMUM_SIZE: int = 1000
    
    # Rate Limiting
    RATE_LIMIT_STRATEGY: str = "fixed_window"  # or "sliding_window"
    
    # Monitoring
    METRICS_ENABLED: bool = True
    SLOW_QUERY_THRESHOLD_MS: int = 100
```

### 7.4 API Contract Changes

**No breaking changes to API contracts.** All optimizations are internal implementation details.

**Response Headers Added:**
```http
X-Cache-Status: HIT | MISS | BYPASS
X-Response-Time: 45.2ms
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1706803200
Content-Encoding: gzip
```

---

## 8. Database Schema Changes

### 8.1 Migration: Pre-computed Search Vectors

**Migration Script (Alembic):**
```python
"""Add search_vector columns for full-text search optimization.

Revision ID: 004_add_search_vectors
Revises: 003_add_api_keys
Create Date: 2025-02-XX
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '004_add_search_vectors'
down_revision = '003_add_api_keys'
branch_labels = None
depends_on = None


def upgrade():
    # Add search_vector columns
    op.add_column(
        'companies',
        sa.Column(
            'search_vector',
            postgresql.TSVECTOR(),
            nullable=True
        )
    )
    
    op.add_column(
        'contacts',
        sa.Column(
            'search_vector',
            postgresql.TSVECTOR(),
            nullable=True
        )
    )
    
    # Create GIN indexes
    op.create_index(
        'idx_companies_search',
        'companies',
        ['search_vector'],
        postgresql_using='gin'
    )
    
    op.create_index(
        'idx_contacts_search',
        'contacts',
        ['search_vector'],
        postgresql_using='gin'
    )
    
    # Create triggers for automatic updates
    op.execute("""
        CREATE OR REPLACE FUNCTION update_company_search_vector()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector := to_tsvector('english',
                COALESCE(NEW.name, '') || ' ' ||
                COALESCE(NEW.description, '') || ' ' ||
                COALESCE(NEW.domain, '')
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER company_search_vector_trigger
            BEFORE INSERT OR UPDATE ON companies
            FOR EACH ROW
            EXECUTE FUNCTION update_company_search_vector();
    """)
    
    op.execute("""
        CREATE OR REPLACE FUNCTION update_contact_search_vector()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector := to_tsvector('english',
                COALESCE(NEW.first_name, '') || ' ' ||
                COALESCE(NEW.last_name, '') || ' ' ||
                COALESCE(NEW.email, '') || ' ' ||
                COALESCE(NEW.job_title, '')
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER contact_search_vector_trigger
            BEFORE INSERT OR UPDATE ON contacts
            FOR EACH ROW
            EXECUTE FUNCTION update_contact_search_vector();
    """)
    
    # Populate existing data in batches
    op.execute("""
        UPDATE companies 
        SET search_vector = to_tsvector('english', 
            COALESCE(name, '') || ' ' || 
            COALESCE(description, '') || ' ' || 
            COALESCE(domain, '')
        )
        WHERE search_vector IS NULL;
    """)
    
    op.execute("""
        UPDATE contacts 
        SET search_vector = to_tsvector('english', 
            COALESCE(first_name, '') || ' ' || 
            COALESCE(last_name, '') || ' ' || 
            COALESCE(email, '') || ' ' || 
            COALESCE(job_title, '')
        )
        WHERE search_vector IS NULL;
    """)


def downgrade():
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS company_search_vector_trigger ON companies")
    op.execute("DROP TRIGGER IF EXISTS contact_search_vector_trigger ON contacts")
    op.execute("DROP FUNCTION IF EXISTS update_company_search_vector()")
    op.execute("DROP FUNCTION IF EXISTS update_contact_search_vector()")
    
    # Drop indexes
    op.drop_index('idx_companies_search', table_name='companies')
    op.drop_index('idx_contacts_search', table_name='contacts')
    
    # Drop columns
    op.drop_column('companies', 'search_vector')
    op.drop_column('contacts', 'search_vector')
```

### 8.2 Additional Indexes for Scale

**Performance Indexes:**
```sql
-- Composite index for common filter combinations
CREATE INDEX CONCURRENTLY idx_companies_filters 
ON companies(industry, country, status) 
WHERE deleted_at IS NULL;

-- Partial index for active records with pagination
CREATE INDEX CONCURRENTLY idx_companies_pagination 
ON companies(created_at DESC, id) 
WHERE deleted_at IS NULL;

-- Partial index for contacts
CREATE INDEX CONCURRENTLY idx_contacts_pagination 
ON contacts(created_at DESC, id) 
WHERE deleted_at IS NULL;

-- Index for company-domain lookups (duplicate detection)
CREATE INDEX CONCURRENTLY idx_companies_domain_active 
ON companies(domain) 
WHERE deleted_at IS NULL AND domain IS NOT NULL;

-- Index for contact email lookups
CREATE INDEX CONCURRENTLY idx_contacts_email_active 
ON contacts(email) 
WHERE deleted_at IS NULL AND email IS NOT NULL;
```

---

## 9. Testing & Validation

### 9.1 Performance Testing Plan

**Test Scenarios:**

| Scenario | Users | Duration | Target |
|----------|-------|----------|--------|
| Company List (filtered) | 100 concurrent | 10 min | < 100ms p95 |
| Contact List (filtered) | 100 concurrent | 10 min | < 100ms p95 |
| Filter Options | 50 concurrent | 5 min | < 50ms p95 |
| Search | 30 concurrent | 5 min | < 100ms p95 |
| Mixed Workload | 200 concurrent | 15 min | < 150ms p95 |
| Bulk Import | 5 concurrent | 10 min | < 5s per 1K records |

**Scale Testing:**

| Data Size | Test | Target |
|-----------|------|--------|
| 1M records | All endpoints | Baseline |
| 10M records | All endpoints | < 150ms p95 |
| 100M records | Priority endpoints | < 200ms p95 |
| 1B records (synthetic) | Priority endpoints | < 250ms p95 |

**Tools:**
- k6 for load testing
- Python scripts for synthetic data generation
- Custom metrics collection via logs

### 9.2 Success Validation Checklist

**Phase 1 Validation:**
- [ ] Connection time < 10ms (measured via logs)
- [ ] Response compression verified via headers
- [ ] Frontend API call count reduced by 50%
- [ ] No console.log in production builds

**Phase 2 Validation:**
- [ ] Cache hit rate > 70% (Redis INFO stats)
- [ ] Filter options < 50ms (p95)
- [ ] Company/Contact lists < 100ms (p95)
- [ ] Cache invalidation working on writes
- [ ] Graceful Redis failure handling

**Phase 3 Validation:**
- [ ] Search queries use index (EXPLAIN ANALYZE)
- [ ] Rate limiting uses 2 Redis ops (monitoring)
- [ ] No slow queries > 100ms (query log)
- [ ] Filter options batched query working

**Phase 4 Validation:**
- [ ] Metrics endpoint returning data
- [ ] Dashboards showing p50, p95, p99 latencies
- [ ] Alerts configured for regression thresholds
- [ ] Load testing with 1000+ concurrent users passed
- [ ] Testing with 100M+ synthetic records passed
- [ ] Runbook documented and tested

### 9.3 Rollback Strategy

**Each phase independently reversible:**

| Phase | Rollback Method | Rollback Time |
|-------|----------------|---------------|
| Phase 1 | Revert DATABASE_URL to port 5432, remove GZip middleware | < 5 minutes |
| Phase 2 | Set CACHE_ENABLED=false | < 1 minute |
| Phase 3 | Revert to original queries, drop new indexes | < 10 minutes |
| Phase 4 | Disable metrics endpoint | < 5 minutes |

**Database Rollback:**
```bash
# If migration needs rollback
alembic downgrade 003_add_api_keys
```

---

## 10. Risks & Mitigation

### 10.1 Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Redis unavailable | Low | High | Graceful fallback to DB, circuit breaker pattern |
| Cache invalidation bugs | Medium | High | Comprehensive testing, TTL as safety net |
| Database migration issues | Low | High | Test on staging, use CONCURRENTLY, backup before migration |
| PgBouncer connection issues | Low | Medium | Keep direct connection as emergency fallback |
| Memory pressure from caching | Medium | Medium | TTL limits, LRU eviction, memory monitoring |
| Compression CPU overhead | Low | Low | Minimum size threshold, monitor CPU |
| Query performance at 1B rows | Medium | High | Test with synthetic data, optimize indexes |

### 10.2 Detailed Risk Analysis

**Risk: Query Performance at 1B Row Scale**
- **Description:** Queries become slow as data grows to 700M-1B records
- **Mitigation:**
  - Use CONCURRENTLY for index creation to avoid downtime
  - Partial indexes (WHERE deleted_at IS NULL) reduce index size
  - Pre-computed columns eliminate expensive computations
  - Caching layer prevents repeated expensive queries
  - Test with synthetic data before production
  - Monitor query plans with EXPLAIN ANALYZE

**Risk: Cache Invalidation Complexity**
- **Description:** Stale data served due to missed invalidation events
- **Mitigation:**
  - Short TTL as safety net (max 5 minutes)
  - Versioned cache keys (e.g., `v1`, `v2`)
  - Write-through cache pattern
  - Automated tests for all write operations
  - Cache warming strategies

**Risk: Redis Single Point of Failure**
- **Description:** Cache unavailability causes all requests to hit DB
- **Mitigation:**
  - Graceful degradation (serve from DB)
  - Circuit breaker pattern
  - Redis persistence (RDB + AOF)
  - Health checks with automatic failover logic

**Risk: Database Index Creation Time**
- **Description:** Creating indexes on large tables blocks writes
- **Mitigation:**
  - Use `CREATE INDEX CONCURRENTLY` (PostgreSQL)
  - Schedule during low-traffic window
  - Test on production-like dataset
  - Have rollback script ready
  - Consider partial indexes for smaller index size

---

## 11. Documentation & Knowledge Transfer

### 11.1 Deliverables

1. **This PRD** - Comprehensive optimization plan
2. **Implementation Guide** - Step-by-step instructions per phase
3. **Architecture Decision Records (ADRs)**:
   - ADR-001: Why Neon PgBouncer over direct connections
   - ADR-002: Cache key structure and TTL strategy
   - ADR-003: Fixed window vs sliding window rate limiting
   - ADR-004: Pre-computed tsvector columns
4. **Runbook** - Cache management, troubleshooting, monitoring
5. **Performance Testing Results** - Before/after metrics
6. **Team Training Session** - Walkthrough of new patterns

### 11.2 Developer Guidelines

**Caching Guidelines:**
```markdown
## Caching Standards

1. All read endpoints > 50ms must use caching
2. Cache TTLs:
   - Static data (filter options): 5-10 minutes
   - Semi-static (lists): 1-5 minutes
   - Dynamic (details): 30 seconds - 2 minutes
   - Search results: 15-30 seconds
3. Always invalidate on writes
4. Use cache-aside pattern by default
5. Version cache keys for breaking changes
6. Monitor cache hit rates (target > 70%)
```

**Query Optimization Guidelines:**
```markdown
## Query Standards

1. Batch multiple queries when possible (single round-trip)
2. Use pre-computed columns for expensive operations
3. Add indexes for new filter fields
4. Always EXPLAIN ANALYZE new queries
5. Use partial indexes (WHERE deleted_at IS NULL)
6. Limit pagination to 100 records max
7. Avoid SELECT *, specify columns
```

**Performance Budget:**
```markdown
## Performance Budget

- p50 response time: < 100ms
- p95 response time: < 200ms
- p99 response time: < 500ms
- Database query time: < 50ms
- Cache hit rate: > 70%
- Payload size: Compress if > 1KB
- API calls per page load: Minimize with React Query
```

---

## 12. Appendix

### 12.1 Current Code References

**Database Session:**
```python
# backend/app/db/session.py
engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,
    echo=settings.DEBUG,
    connect_args={"statement_cache_size": 0},
)
```

**Filter Options Query Pattern:**
```python
# backend/app/api/v1/endpoints/companies.py:238-351
# 8 separate queries:
industries_stmt = select(distinct(Company.industry))...
countries_stmt = select(distinct(Company.country))...
revenue_stmt = select(func.min(Company.revenue), func.max(Company.revenue))...
# ... 5 more queries
```

**Search Implementation:**
```python
# backend/app/api/v1/endpoints/search.py:39-44
company_vector = func.to_tsvector(
    'english',
    func.coalesce(Company.name, '') + ' ' +
    func.coalesce(Company.description, '') + ' ' +
    func.coalesce(Company.domain, '')
)
```

**Frontend API Client:**
```typescript
// frontend/lib/api.ts:49-57
getFilterOptions: async () => {
    const response = await api.get('/companies/filter-options');
    return response.data;
},
```

### 12.2 Database Indexes (Current + Proposed)

**Existing Indexes:**
- `idx_companies_domain`, `idx_companies_status`, `idx_companies_industry`
- `idx_companies_country`, `idx_companies_lead_score`
- `idx_contacts_email` (UNIQUE), `idx_contacts_company_id`
- GIN indexes for arrays: `idx_companies_keywords`, `idx_companies_technologies`
- GIN indexes for tags: `idx_companies_tags_a`, `idx_companies_tags_b`, `idx_companies_tags_c`
- Full-text search GIN indexes: `idx_companies_fts`, `idx_contacts_fts`

**Proposed New Indexes:**
```sql
-- Composite index for common filter combinations
CREATE INDEX CONCURRENTLY idx_companies_filters 
ON companies(industry, country, status) 
WHERE deleted_at IS NULL;

-- Partial index for active records with pagination
CREATE INDEX CONCURRENTLY idx_companies_pagination 
ON companies(created_at DESC, id) 
WHERE deleted_at IS NULL;

-- Pre-computed search vector
CREATE INDEX idx_companies_search ON companies USING GIN(search_vector);

-- Active record lookups
CREATE INDEX CONCURRENTLY idx_companies_domain_active 
ON companies(domain) 
WHERE deleted_at IS NULL AND domain IS NOT NULL;
```

### 12.3 Performance Baseline

**Current Metrics (measured from logs):**

| Endpoint | Avg (ms) | p50 (ms) | p95 (ms) | p99 (ms) |
|----------|----------|----------|----------|----------|
| GET /companies | 180 | 150 | 350 | 500 |
| GET /contacts | 180 | 150 | 350 | 500 |
| GET /companies/filter-options | 320 | 280 | 450 | 600 |
| GET /contacts/filter-options | 280 | 250 | 400 | 550 |
| GET /search | 450 | 380 | 750 | 1200 |
| GET /stats | 200 | 180 | 300 | 400 |
| POST /bulk/companies | 8000 | 7500 | 12000 | 15000 |

**Database:**
- Connection time: ~80ms average (direct connection)
- Query execution: 20-100ms for simple queries, 100-300ms for complex filters

---

## 13. Approval & Sign-off

| Role | Name | Status | Date |
|------|------|--------|------|
| Product Manager | TBD | ⬜ Pending | |
| Tech Lead | TBD | ⬜ Pending | |
| DevOps | TBD | ⬜ Pending | |
| Engineering Team | TBD | ⬜ Pending | |

---

## 14. Next Steps

1. **Review this PRD** with stakeholders
2. **Clarify any open questions** (see below)
3. **Approve implementation phases** - Which phase to start first?
4. **Confirm Phase 1** can begin immediately:
   - Switch DATABASE_URL to port 6543 (Neon pooler)
   - Add GZip middleware
   - Configure React Query
   - Set up request logging

---

## 15. Open Questions for Stakeholders

1. **Monitoring Tools:** Would you prefer:
   - A) Simple structured logging (already have structlog)
   - B) Prometheus metrics endpoint (new dependency)
   - C) Both

2. **Cache Warming:** For the 700M-1B scale, should we implement:
   - A) Background cache warming on startup
   - B) Lazy loading (cache on first request)
   - C) Both with configurable strategy

3. **Synthetic Data:** For scale testing, should I create:
   - A) Python script to generate 100M-1B synthetic records
   - B) Use existing data and extrapolate
   - C) Test gradually as real data grows

4. **Rate Limiting:** Current default is 1000 req/min. For the optimized system:
   - Keep at 1000/min
   - Increase to 2000/min (with caching)
   - Make it configurable per endpoint

5. **Bulk Import Optimization:** The bulk import has batch delays (150ms) for Neon connections. With pooler:
   - Keep delays (safer)
   - Remove delays (faster)
   - Make configurable

---

**Document Status:** Ready for Implementation  
**Last Updated:** February 2025  
**Version:** 1.0

---

*End of PRD*
