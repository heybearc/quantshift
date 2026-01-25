# QuantShift Admin - Next.js Setup Guide

**Architecture:** Next.js-only (No FastAPI)  
**Date:** December 26, 2025

---

## 🏗️ Architecture

**Single Next.js Application:**
```
Next.js (Port 3001)
├─ Frontend Pages (React)
├─ API Routes (/app/api/*)
├─ Prisma ORM
└─ PostgreSQL Database
```

**This matches your proven production pattern from LDC Tools and Theoshift!**

---

## 🚀 Setup Instructions

### Step 1: Install Dependencies

```bash
cd apps/admin-web
npm install
```

### Step 2: Set Up Database

```bash
# Generate Prisma client
npm run db:generate

# Push schema to database (creates tables)
npm run db:push

# Create admin user
npm run db:init
```

**Expected Output:**
```
🚀 Initializing QuantShift database...

✅ Admin user created successfully!

📧 Email: corya1992@gmail.com
🔑 Password: admin123
👤 Role: ADMIN
🆔 ID: [uuid]

⚠️  IMPORTANT: Change the password after first login!
```

### Step 3: Start Development Server

```bash
npm run dev
```

**Server will start on:** http://localhost:3001

---

## 🧪 Testing

1. **Open Browser:** http://localhost:3001
   - Should redirect to `/login`

2. **Login:**
   - Email: `corya1992@gmail.com`
   - Password: `admin123`

3. **After Login:**
   - Should redirect to `/dashboard`
   - See bot status, account info
   - See your email and role in header

4. **Test Logout:**
   - Click "Logout" button
   - Should redirect to `/login`

---

## 📁 Project Structure

```
apps/admin-web/
├── app/
│   ├── api/
│   │   └── auth/
│   │       ├── login/route.ts      # POST /api/auth/login
│   │       ├── logout/route.ts     # POST /api/auth/logout
│   │       ├── me/route.ts         # GET /api/auth/me
│   │       └── refresh/route.ts    # POST /api/auth/refresh
│   ├── dashboard/
│   │   └── page.tsx                # Protected dashboard
│   ├── login/
│   │   └── page.tsx                # Login page
│   └── layout.tsx                  # Root layout with AuthProvider
├── components/
│   └── protected-route.tsx         # Protected route wrapper
├── lib/
│   ├── auth.ts                     # Auth utilities (JWT, bcrypt)
│   ├── auth-context.tsx            # Auth context provider
│   └── prisma.ts                   # Prisma client
├── prisma/
│   └── schema.prisma               # Database schema
├── scripts/
│   └── init-db.ts                  # Database initialization
└── .env.local                      # Environment variables
```

---

## 🔐 Environment Variables

**File:** `.env.local`

```env
DATABASE_URL="postgresql://quantshift:Cloudy_92!@localhost:5432/quantshift"
JWT_SECRET="your-secret-key-change-in-production"
NODE_ENV="development"
```

---

## 📊 Database Schema

**Tables:**
- `users` - User accounts with authentication
- `sessions` - Refresh token storage
- `audit_log` - Action tracking

**User Roles:**
- `ADMIN` - Full access
- `VIEWER` - Read-only access

---

## 🔧 Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run db:generate  # Generate Prisma client
npm run db:push      # Push schema to database
npm run db:migrate   # Create migration
npm run db:init      # Initialize database with admin user
```

---

## 🎯 API Endpoints

All endpoints are Next.js API routes:

**Authentication:**
- `POST /api/auth/login` - Login with email/password
- `POST /api/auth/logout` - Logout and revoke tokens
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user

**Future Endpoints:**
- `/api/users` - User management
- `/api/bot` - Bot control
- `/api/email` - Email configuration
- `/api/trades` - Trading data

---

## 🔒 Security Features

1. **JWT Tokens:**
   - Access token: 15 minutes
   - Refresh token: 7 days

2. **httpOnly Cookies:**
   - XSS protection
   - Secure in production
   - SameSite=lax

3. **Password Hashing:**
   - bcrypt with cost 12
   - Automatic salting

4. **Token Revocation:**
   - Refresh tokens stored in database
   - Revoked on logout

---

## 🐛 Troubleshooting

### Database Connection Error:
```bash
# Check PostgreSQL is running
psql -U quantshift -d quantshift -h localhost

# If database doesn't exist:
createdb -U quantshift quantshift
```

### Prisma Client Error:
```bash
# Regenerate Prisma client
npm run db:generate
```

### Port Already in Use:
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

---

## ✅ Production Deployment

**Container:** quantshift-dashboard (to be renamed)

**Services:**
- Next.js: PM2 process on port 3000
- PostgreSQL: Shared database container
- Nginx: Reverse proxy

**Environment:**
- Set `NODE_ENV=production`
- Use strong `JWT_SECRET`
- Enable HTTPS
- Configure proper CORS

---

## 📝 Next Steps

After successful testing:

1. **Week 2:** User management UI
2. **Week 3:** Email configuration UI
3. **Week 4:** Bot monitoring with real data
4. **Week 5:** Bot control panel

---

## 🎉 Benefits of Next.js-Only

✅ **Single technology stack** (TypeScript everywhere)  
✅ **Proven in production** (LDC Tools, Theoshift)  
✅ **Simpler deployment** (one service)  
✅ **Better stability** (no FastAPI issues)  
✅ **End-to-end type safety** (Prisma + TypeScript)  
✅ **Faster development** (no context switching)

---

**Ready to test!** Just run `npm run dev` and open http://localhost:3001
