# QuantShift Admin Platform - Deployment Guide

## Critical Lesson Learned: Stale Build Issue (Jan 4, 2025)

### What Went Wrong
After code updates, the application showed **completely broken styling** (unstyled HTML) even though:
- CSS files existed on disk
- Server returned HTTP 200 for CSS requests
- HTML contained correct `<link>` tags
- curl tests showed valid CSS content

### Root Cause
**Stale `.next` build directory** with mismatched build artifacts:
- Old build ID cached in Next.js server
- CSS file references pointing to non-existent/old files
- Next.js serving cached pages from previous build
- Browser receiving 404s for CSS files that appeared to exist

### The Fix
```bash
rm -rf .next
rm -rf node_modules/.cache
npm run build
```

Complete rebuild from scratch resolved the issue immediately.

---

## Deployment Checklist

### ✅ ALWAYS Do This When Deploying

1. **Clean build artifacts first**
   ```bash
   rm -rf .next
   rm -rf node_modules/.cache
   ```

2. **Pull latest code**
   ```bash
   cd /opt/quantshift
   git pull origin main
   ```

3. **Install dependencies** (if package.json changed)
   ```bash
   cd apps/admin-web
   npm install --production
   ```

4. **Build from scratch**
   ```bash
   npm run build
   ```

5. **Verify build succeeded**
   ```bash
   cat .next/BUILD_ID  # Should show new build ID
   ```

6. **Restart cleanly**
   ```bash
   ./scripts/restart.sh
   ```

### ❌ NEVER Do This

- ❌ Run `npm run build` without cleaning `.next` first
- ❌ Restart PM2 without rebuilding after code changes
- ❌ Assume CSS issues are "browser cache" - check build first
- ❌ Skip verifying the build ID after deployment

---

## Quick Deployment Commands

### Use the deployment script (RECOMMENDED)
```bash
ssh root@10.92.3.29
cd /opt/quantshift/apps/admin-web
./scripts/deploy.sh
```

### Manual deployment (if script fails)
```bash
ssh root@10.92.3.29
cd /opt/quantshift/apps/admin-web

# Clean
rm -rf .next node_modules/.cache

# Pull & Build
cd /opt/quantshift && git pull origin main
cd apps/admin-web
npm install --production
npm run build

# Restart
./scripts/restart.sh
```

---

## Troubleshooting

### Styling is broken / CSS not loading

**First check:** Is this a stale build?
```bash
# On container
cat /opt/quantshift/apps/admin-web/.next/BUILD_ID

# Compare to what browser is requesting
curl -s http://localhost:3001/login | grep buildId
```

If build IDs don't match → **Clean rebuild required**

### Port 3001 already in use

```bash
# Find and kill the process
lsof -ti:3001 | xargs kill -9

# Or use restart script (handles this automatically)
./scripts/restart.sh
```

### PM2 shows "errored" status

```bash
# Check logs
pm2 logs quantshift-admin --lines 50

# Common issue: Port conflict
# Solution: Use restart script
./scripts/restart.sh
```

---

## Infrastructure

- **Container:** LXC 137 (10.92.3.29)
- **Database:** Container 131 (10.92.3.21)
- **Port:** 3001
- **PM2 Process:** quantshift-admin
- **Root Password:** Cloudy_92!

---

## What We Were Working On (Before This Issue)

You were implementing:
1. ✅ Version bump to 1.1.0
2. ✅ Help documentation page
3. ✅ Automated release notes system
4. ✅ Version banner display
5. ✅ Release notes moved to Help page footer

All features are now deployed and working correctly.
