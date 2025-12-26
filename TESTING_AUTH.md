# Testing the Authentication System

**Date:** December 26, 2025

---

## 🎯 What We Built

Complete authentication system with:
- **Backend:** FastAPI with JWT tokens, httpOnly cookies
- **Frontend:** Next.js with login page, auth context, protected routes
- **Database:** PostgreSQL with User, Session, AuditLog models

---

## 🚀 How to Test

### Architecture Overview

**Single Container Setup (like LDC Construction Tools):**
- Next.js frontend: Port 3000
- FastAPI backend: Port 8000
- Next.js proxies `/api/*` requests to FastAPI
- Both run in same container/environment

### Step 1: Start the Backend (FastAPI)

**Terminal 1:**
```bash
# Navigate to backend
cd apps/admin-api

# Create virtual environment (if not exists)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database and create admin user
python scripts/init_db.py

# Start FastAPI server
uvicorn main:app --reload --port 8000
```

**Expected Output:**
```
Creating database tables...
✓ Database tables created

✓ Admin user created: corya1992@gmail.com
  ID: [uuid]
  Role: admin

Database initialization complete!

Admin credentials:
  Email: corya1992@gmail.com
  Password: admin123
```

**Backend running at:** http://localhost:8000

---

### Step 2: Start the Frontend (Next.js)

**Terminal 2:**
```bash
# Navigate to frontend
cd apps/admin-web

# Install dependencies (if not done)
npm install

# Start development server
npm run dev
```

**Frontend running at:** http://localhost:3000

**API Proxy:** Next.js automatically proxies `/api/*` to `http://localhost:8000/api/*`

---

### Step 3: Test the Authentication Flow

1. **Open Browser:** http://localhost:3000
   - Should redirect to `/login`

2. **Login:**
   - Email: `corya1992@gmail.com`
   - Password: `admin123`
   - Click "Sign in"

3. **After Login:**
   - Should redirect to `/dashboard`
   - See welcome message
   - See bot status, account balance, etc.
   - See your email and role in header

4. **Test Logout:**
   - Click "Logout" button in header
   - Should redirect back to `/login`
   - Tokens should be cleared

5. **Test Protected Routes:**
   - Try accessing `/dashboard` without logging in
   - Should redirect to `/login`

---

## 🔍 API Endpoints to Test

### Health Check
```bash
curl http://localhost:8000/
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"corya1992@gmail.com","password":"admin123"}' \
  -c cookies.txt
```

### Get Current User
```bash
curl http://localhost:8000/api/auth/me \
  -b cookies.txt
```

### Logout
```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -b cookies.txt
```

---

## 📊 Database Tables

After running `init_db.py`, you should have:

**Users Table:**
- 1 admin user (corya1992@gmail.com)
- Password: admin123 (hashed with bcrypt)
- Role: admin

**Sessions Table:**
- Empty initially
- Populated when users login
- Stores refresh token hashes

**Audit Log Table:**
- Empty initially
- Will track all user actions

---

## 🔐 Security Features

1. **JWT Tokens:**
   - Access token: 15 minutes expiration
   - Refresh token: 7 days expiration

2. **httpOnly Cookies:**
   - Prevents XSS attacks
   - Tokens not accessible via JavaScript

3. **Secure Cookies:**
   - HTTPS only in production
   - SameSite=lax for CSRF protection

4. **Password Hashing:**
   - bcrypt with cost factor 12
   - Salted automatically

5. **Token Revocation:**
   - Refresh tokens stored in database
   - Can be revoked on logout

---

## 🐛 Troubleshooting

### Backend won't start:
```bash
# Check if PostgreSQL is running
psql -U quantshift -d quantshift -h localhost

# If database doesn't exist, create it:
createdb -U quantshift quantshift
```

### Frontend won't start:
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### CORS errors:
- Make sure backend is running on port 8000
- Make sure frontend is running on port 3000
- CORS is configured for localhost:3000 in backend

### Login fails:
- Check backend logs for errors
- Verify database has admin user
- Try re-running `python scripts/init_db.py`

---

## ✅ Success Criteria

- [x] Backend starts without errors
- [x] Database tables created
- [x] Admin user created
- [x] Frontend starts without errors
- [x] Can access login page
- [x] Can login with admin credentials
- [x] Redirects to dashboard after login
- [x] Dashboard shows user info
- [x] Can logout successfully
- [x] Protected routes redirect to login

---

## 🎯 Next Steps

After successful testing:

1. **Week 2:** User management UI (create/edit/delete users)
2. **Week 3:** Email configuration UI
3. **Week 4:** Bot monitoring dashboard with real data
4. **Week 5:** Bot control panel (start/stop/restart)

---

## 📝 Notes

- Default admin password is `admin123` - **change this in production!**
- Backend runs on port 8000
- Frontend runs on port 3000
- Database: PostgreSQL on localhost:5432
- Redis: localhost:6379 (for future session storage)
