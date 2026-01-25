# QuantShift Restructure Plan

## Current Structure (Confusing)
```
quantshift/apps/
├── admin-web/        ← Deployed to trader.cloudigan.net
│   └── app/
│       ├── login/
│       ├── admin/
│       ├── dashboard/
│       └── ...
├── dashboard/        ← Not deployed, has tests
│   └── src/app/
│       ├── bots/
│       ├── positions/
│       └── ...
└── admin-api/        ← Backend
```

## New Structure (Standard Next.js)
```
quantshift/
├── app/                      ← Single Next.js app
│   ├── (auth)/              ← Route group for auth pages
│   │   ├── login/
│   │   ├── verify-email/
│   │   └── accept-invitation/
│   ├── (public)/            ← Route group for public pages
│   │   └── dashboard/       ← Public trading dashboard
│   ├── (protected)/         ← Route group for authenticated pages
│   │   ├── admin/           ← Admin panel
│   │   ├── bots/            ← Bot management
│   │   ├── positions/       ← Position tracking
│   │   ├── trades/          ← Trade history
│   │   ├── performance/     ← Performance metrics
│   │   └── settings/        ← User settings
│   ├── api/                 ← API routes
│   ├── layout.tsx           ← Root layout
│   └── page.tsx             ← Home page
├── components/              ← Shared components
├── lib/                     ← Utilities and helpers
├── tests/                   ← All tests in one place
│   ├── smoke-test.spec.ts
│   ├── auth.spec.ts
│   ├── admin.spec.ts
│   ├── trading.spec.ts
│   └── test-helpers.ts
├── public/                  ← Static assets
├── prisma/                  ← Database schema
└── package.json             ← Single package.json

apps/
└── admin-api/               ← Keep separate backend API
```

## Migration Steps

### 1. Create New Structure
- Create main app directory with route groups
- Set up proper Next.js 14 app router structure

### 2. Migrate Admin-Web Features
- Move all routes from admin-web/app to new structure
- Organize into route groups (auth, public, protected)
- Keep all authentication logic
- Preserve all admin features

### 3. Migrate Dashboard Features
- Move trading dashboard components
- Integrate with main app
- Make dashboard accessible at /dashboard

### 4. Consolidate Tests
- Move all tests to single tests/ directory
- Update test paths and imports
- Configure for single app testing

### 5. Update Configuration
- Single package.json with all dependencies
- Single tsconfig.json
- Single next.config.js
- Update environment variables

### 6. Update Deployment
- Deploy single app to trader.cloudigan.net
- Update PM2 configuration
- Test all routes work correctly

## Benefits

✅ **Standard Next.js structure** - Anyone can understand it
✅ **Single app to deploy** - Simpler deployment
✅ **Single test suite** - Easy to test everything
✅ **Intuitive routing** - /login, /dashboard, /admin makes sense
✅ **Shared authentication** - One auth system for everything
✅ **Better performance** - No duplicate code or dependencies

## Testing After Migration

```bash
# Test login
curl https://trader.cloudigan.net/login

# Test dashboard
curl https://trader.cloudigan.net/dashboard

# Test admin
curl https://trader.cloudigan.net/admin

# Run all tests
cd /Users/cory/Documents/Cloudy-Work/applications/quantshift
npm run test:e2e
```

## Rollback Plan

If anything goes wrong:
1. Keep old apps/ directory as backup
2. Can quickly redeploy admin-web
3. All data in database remains unchanged

---

**Status:** Ready to execute
**Estimated Time:** 30-45 minutes
**Risk:** Low (keeping backups)
