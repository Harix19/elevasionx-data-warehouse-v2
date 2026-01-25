## Epic 6 - Quick Start Guide

**Login Credentials:**
```
Email: admin@example.com
Password: adminpass123
```

**Issue:** Database is auto-suspended on Neon Serverless. The first connection will activate it but may timeout.

**Solution:** Use these credentials to login. The first attempt may fail with a database error - just **try again** and it should work after the database wakes up.

---

## Start Servers

**Backend:**
```bash
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
bun run dev
```

---

## Access Application

1. Go to: http://localhost:3000
2. Login with credentials above
3. If you get a database error, wait 5 seconds and refresh
4. The Neon database will activate on the second attempt

---

## Next: UI Improvements

I'm now going to improve the UI design using the frontend-design skill.
