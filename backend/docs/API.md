# API Documentation

Complete API documentation for the Leads Data Warehouse.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

This API supports two authentication methods:

### 1. JWT Bearer Token

Used for user sessions and full admin access.

**Header:**
```
Authorization: Bearer <jwt_token>
```

**Get a token:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your@email.com&password=yourpassword"
```

### 2. API Key

Used for programmatic access with specific permissions.

**Header:**
```
X-API-Key: ldwsk-xxxxxxxxxxxxxxxxxxxxxxxx
```

**Generate API key:**
```bash
curl -X POST http://localhost:8000/api/v1/api-keys/ \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production API",
    "access_level": "write",
    "rate_limit": 1000
  }'
```

**Important:** The API key is only shown once during creation. Save it immediately!

## Access Levels

API keys have three access levels:

| Level | Description | Endpoints |
|-------|-------------|-----------|
| `read` | Read-only access | GET endpoints (companies, contacts, search, export) |
| `write` | Full CRUD access | All endpoints except API key management |
| `admin` | Full access | All endpoints including API key management |

## Rate Limiting

All requests are rate limited to prevent abuse.

**Default:** 1000 requests per minute  
**Custom:** Configurable per API key (1-10000 req/min)

**Headers:**
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets

**Rate limit exceeded:**
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 45
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1706652000
```

## Endpoints

### Companies

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/companies` | read | List companies with filters |
| POST | `/companies` | write | Create new company |
| GET | `/companies/{id}` | read | Get company by ID |
| PATCH | `/companies/{id}` | write | Update company |
| DELETE | `/companies/{id}` | write | Soft delete company |
| POST | `/companies/{id}/restore` | write | Restore deleted company |
| GET | `/companies/filter-options` | read | Get available filter values |
| GET | `/companies/{id}/contacts` | read | Get company's contacts |

### Contacts

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/contacts` | read | List contacts with filters |
| POST | `/contacts` | write | Create new contact |
| GET | `/contacts/{id}` | read | Get contact by ID |
| PATCH | `/contacts/{id}` | write | Update contact |
| DELETE | `/contacts/{id}` | write | Soft delete contact |
| POST | `/contacts/{id}/restore` | write | Restore deleted contact |
| GET | `/contacts/filter-options` | read | Get available filter values |

### Search

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/search` | read | Full-text search across all entities |

### Bulk Operations

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/bulk/import` | write | Import CSV file (companies or contacts) |
| POST | `/bulk/companies` | write | Bulk create/update companies via JSON |
| POST | `/bulk/contacts` | write | Bulk create/update contacts via JSON |

### Export

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/export/companies` | read | Export companies as CSV |
| GET | `/export/contacts` | read | Export contacts as CSV |

### Stats

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/stats` | read | Get dashboard statistics |

### API Keys (Admin Only)

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/api-keys/` | admin | Create new API key |
| GET | `/api-keys/` | admin | List all API keys |
| GET | `/api-keys/{id}` | admin | Get API key details |
| PATCH | `/api-keys/{id}` | admin | Update API key |
| DELETE | `/api-keys/{id}` | admin | Revoke API key |
| POST | `/api-keys/{id}/regenerate` | admin | Regenerate API key |

### Authentication

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/auth/token` | public | Get JWT token |
| GET | `/users/me` | read | Get current user info |

## Filtering

### Companies

**Available filters:**
- `industry`: Filter by industry name
- `country`: Filter by country code
- `status`: Filter by lead status
- `min_employee_count` / `max_employee_count`: Employee count range
- `min_revenue` / `max_revenue`: Revenue range
- `tags`: Comma-separated custom tags (matches ANY tag field)

**Example:**
```bash
curl "http://localhost:8000/api/v1/companies?industry=Software&country=US&min_employee_count=50"
```

### Contacts

**Available filters:**
- `seniority_level`: Filter by seniority
- `department`: Filter by department
- `status`: Filter by lead status
- `company_id`: Filter by company UUID
- `tags`: Comma-separated custom tags (matches ANY tag field)

**Example:**
```bash
curl "http://localhost:8000/api/v1/contacts?seniority_level=Executive&department=Sales"
```

## Pagination

All list endpoints support cursor-based pagination:

**Parameters:**
- `cursor`: Opaque cursor for next page (omit for first page)
- `limit`: Items per page (default: 20, max: 100)

**Response:**
```json
{
  "items": [...],
  "total": 150,
  "next_cursor": "eyJpZCI6IDEyM30=",
  "has_more": true
}
```

**Example:**
```bash
# First page
curl "http://localhost:8000/api/v1/companies?limit=50"

# Next page
curl "http://localhost:8000/api/v1/companies?limit=50&cursor=eyJpZCI6IDEyM30="
```

## Tag Filtering

Tags support both OR and AND logic:

**OR logic (default):** Any of the tags match
```bash
curl "http://localhost:8000/api/v1/companies?tags=startup,fintech"
```

**AND logic:** All tags must match
```bash
curl "http://localhost:8000/api/v1/companies?tags=startup&tags=fintech"
```

## Import CSV

Upload CSV files for bulk import:

```bash
curl -X POST "http://localhost:8000/api/v1/bulk/import?type=companies" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@companies.csv"
```

## Error Handling

The API returns standard HTTP status codes:

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 202 | Accepted (async operation) |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden (insufficient access) |
| 404 | Not Found |
| 429 | Rate Limit Exceeded |
| 500 | Internal Server Error |

**Error response format:**
```json
{
  "detail": "Error message here"
}
```

## Health Checks

**Liveness:**
```bash
curl http://localhost:8000/health/live
```

**Readiness (includes database check):**
```bash
curl http://localhost:8000/health/ready
```

## OpenAPI / Swagger UI

Interactive API documentation is available at:

```
http://localhost:8000/docs
```

## Postman Collection

Import the collection from `docs/postman_collection.json` and the environment from `docs/postman_environment.json`.

## SDK Generation

Generate client SDKs from the OpenAPI spec:

```bash
# Generate Python SDK
openapi-generator-cli generate -i docs/openapi.yaml -g python -o sdk/python

# Generate TypeScript SDK
openapi-generator-cli generate -i docs/openapi.yaml -g typescript-axios -o sdk/typescript
```
