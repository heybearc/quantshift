---
description: Automated testing workflow for pre-deployment validation
---

# /test-release - Automated Testing Workflow

Run automated tests before deploying to verify all functionality works correctly.

## Quick Usage

```bash
# Run smoke tests (1-2 minutes)
npm run test:smoke:quick

# Test against staging/production server
BASE_URL=<server_url> TEST_USER_EMAIL=admin@quantshift.local TEST_USER_PASSWORD='Admin123!' npm run test:smoke:quick
```

## Full Workflow

### Step 1: Setup (First Time Only)
```bash
# Verify .env.test exists with correct credentials
cat .env.test

# Should contain:
# TEST_USER_EMAIL=admin@quantshift.local
# TEST_USER_PASSWORD=Admin123!
# BASE_URL=http://localhost:3000
```

### Step 2: Run Tests Before Deployment
```bash
# Quick smoke tests (recommended before every deployment)
npm run test:smoke:quick
```

**Expected:** All tests pass ✅ in 1-2 minutes

### Step 3: Deploy to Staging/Production
```bash
# Your deployment commands
git push origin feature-branch
# Deploy to your server
```

### Step 4: Test Deployed Environment
```bash
# Test against deployed server
BASE_URL=<server_url> TEST_USER_EMAIL=admin@quantshift.local TEST_USER_PASSWORD='Admin123!' npm run test:smoke:quick
```

**Expected:** All tests pass ✅ on deployed environment

---

## Available Test Commands

```bash
# Quick smoke tests (fastest, recommended)
npm run test:smoke:quick

# All smoke tests
npm run test:smoke

# All E2E tests
npm run test:e2e

# E2E tests with UI
npm run test:e2e:ui

# Debug mode
npm run test:debug

# View last test report
npm run test:report
```

---

## What Gets Tested

### Smoke Tests (Quick - 1-2 min)
- ✅ Login flow with test credentials
- ✅ Dashboard loads successfully
- ✅ No critical JavaScript errors
- ✅ Basic navigation works

---

## Troubleshooting

### Tests Failing?

1. **Check test user exists:**
   ```bash
   # Verify admin@quantshift.local user exists on server
   # User must have ADMIN role and ACTIVE status
   ```

2. **Check server is running:**
   ```bash
   curl <server_url>/login
   # Should return 200 OK
   ```

3. **Check credentials:**
   ```bash
   # Verify .env.test has correct credentials
   cat .env.test
   ```

4. **View detailed logs:**
   ```bash
   npm run test:e2e:headed
   # Opens browser to see what's happening
   ```

5. **Check screenshots/videos:**
   ```bash
   ls test-results/
   # Contains screenshots and videos of failures
   ```

---

## Best Practices

1. **Always test on staging first** before production
2. **Run smoke tests before every deployment**
3. **Check test results** before proceeding with release
4. **Keep test credentials secure** - never commit to git
5. **Update tests** when adding new features

---

## Integration with Deployment Workflow

```bash
# Recommended deployment flow:
1. npm run test:smoke:quick              # Test locally
2. git push origin feature-branch        # Push code
3. Deploy to staging                     # Deploy
4. BASE_URL=<staging> npm run test:smoke:quick  # Test staging
5. If tests pass → deploy to production
6. BASE_URL=<production> npm run test:smoke:quick  # Test production
```

---

## Time Savings

**Manual Testing:** 15-20 minutes per deployment
**Automated Testing:** 1-2 minutes per deployment

**Savings:** ~18 minutes per deployment × multiple deployments per week = significant time saved!

---

## Support

For issues with automated testing:
1. Check `TESTING.md` for detailed documentation
2. Review `TESTING-CHECKLIST.md` for manual verification steps
3. Check test screenshots in `test-results/` directory
