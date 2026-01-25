# Migration Gotchas

## SQLAlchemy ENUM Types

When using `postgresql.ENUM` in Alembic migrations:

### ❌ DON'T do this:
```python
lead_status = postgresql.ENUM(..., name='lead_status', create_type=True)
lead_status.create(op.get_bind(), checkfirst=True)  # Redundant!
```

### ✅ DO this instead:
```python
lead_status = postgresql.ENUM(..., name='lead_status', create_type=True)
# Let SQLAlchemy handle creation when the type is first used
```

## Why This Matters

- `create_type=True` tells SQLAlchemy to automatically create the ENUM when first referenced
- Calling `.create()` explicitly with `checkfirst=True` seems safe but creates a race condition
- The type gets created once, then the second attempt fails with "already exists"

## Production Safety

Cleanup scripts should never run in production. Always:
1. Check environment variables before executing
2. Require user confirmation for destructive operations
3. Log warnings prominently

Example:
```python
env = os.getenv("ENV", "").lower()
if env not in ("dev", "development", "test"):
    print(f"ERROR: Cleanup script can only run in development environment. Current ENV={env}")
    sys.exit(1)

response = input("Type 'yes' to continue: ")
if response.lower() != "yes":
    print("Cleanup cancelled.")
    sys.exit(0)
```
