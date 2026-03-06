# MCP Deployment Tool Workaround

**Issue:** D-QS-015 - MCP Tool State Tracking Issue  
**Created:** 2026-03-06  
**Status:** Active Workaround

---

## Problem

The MCP `deploy_to_standby` tool has a state tracking issue where it always deploys to BLUE (10.92.3.29) regardless of which server is actually LIVE or STANDBY according to HAProxy routing.

**Symptoms:**
- MCP tool reports "Deployment to STANDBY complete"
- Tool shows BLUE as STANDBY in status output
- However, HAProxy may actually be routing production traffic to BLUE
- Result: Deployment goes to wrong server, production doesn't get the update

**Example:**
```bash
# MCP tool says:
LIVE: GREEN (10.92.3.30)
STANDBY: BLUE (10.92.3.29)

# But HAProxy actually routes:
Production traffic → BLUE (10.92.3.29)
```

---

## Root Cause

The MCP tool maintains internal state about which server is LIVE/STANDBY but doesn't verify this against HAProxy configuration before deploying. This causes drift between tool state and actual traffic routing.

---

## Workaround

### Step 1: Verify Actual LIVE Server

Always check HAProxy configuration to determine which server is actually serving production traffic:

```bash
# Method 1: Use MCP status (but verify against HAProxy)
mcp0_get_deployment_status --app quantshift

# Method 2: Direct HAProxy query (authoritative)
ssh root@10.92.3.26 "grep 'use_backend.*if is_quantshift' /etc/haproxy/haproxy.cfg"
```

**Expected output:**
- `use_backend quantshift-blue-backend if is_quantshift` → BLUE is LIVE
- `use_backend quantshift-green-backend if is_quantshift` → GREEN is LIVE

### Step 2: Deploy to Correct Server

Deploy directly to the server that needs the update via SSH:

#### If deploying to BLUE (10.92.3.29):
```bash
ssh root@10.92.3.29 "cd /opt/quantshift/apps/web && \
  git pull origin main && \
  npm install && \
  npm run build && \
  pm2 restart quantshift-blue"
```

#### If deploying to GREEN (10.92.3.30):
```bash
ssh root@10.92.3.30 "cd /opt/quantshift/apps/web && \
  git pull origin main && \
  npm install && \
  npm run build && \
  pm2 restart quantshift-green"
```

### Step 3: Verify Deployment

```bash
# Check HTTP status
curl -s -o /dev/null -w "%{http_code}" https://quantshift.io/your-new-route

# Expected: 200

# Verify PM2 process restarted
ssh root@10.92.3.XX "pm2 list"
```

---

## Deployment Scenarios

### Scenario 1: Deploy to STANDBY for Testing

1. Check HAProxy to identify STANDBY server
2. Deploy to STANDBY via SSH (see Step 2)
3. Test on direct URL: `http://blue.quantshift.io` or `http://green.quantshift.io`
4. If tests pass, switch traffic via MCP or HAProxy

### Scenario 2: Deploy to LIVE (Production)

1. Check HAProxy to identify LIVE server
2. Deploy to LIVE via SSH (see Step 2)
3. Verify on production URL: `https://quantshift.io`
4. Monitor for issues

### Scenario 3: Deploy to Both Servers

If you need both servers to have the same code:

```bash
# Deploy to BLUE
ssh root@10.92.3.29 "cd /opt/quantshift/apps/web && \
  git pull origin main && npm install && npm run build && pm2 restart quantshift-blue"

# Deploy to GREEN
ssh root@10.92.3.30 "cd /opt/quantshift/apps/web && \
  git pull origin main && npm install && npm run build && pm2 restart quantshift-green"
```

---

## Long-Term Fix

The MCP tool needs to be updated to:

1. Query HAProxy configuration before deployment
2. Determine actual LIVE/STANDBY status from HAProxy
3. Deploy to correct server based on HAProxy routing
4. Update internal state to match HAProxy reality

**Tracked in:** D-QS-015 (DECISIONS.md)

---

## Related Documentation

- `BLUE-GREEN-SWITCHING.md` - Traffic switching procedures
- `HAPROXY-QUANTSHIFT-CONFIG.md` - HAProxy configuration
- `DECISIONS.md` - D-QS-015 (MCP tool state tracking issue)
- `.cloudy-work/_cloudy-ops/context/DECISIONS.md` - D-008 (HAProxy is source of truth)

---

## Quick Reference

**Always verify HAProxy first:**
```bash
ssh root@10.92.3.26 "grep 'use_backend.*if is_quantshift' /etc/haproxy/haproxy.cfg"
```

**Deploy to server that needs update:**
```bash
# Replace XX with 29 (BLUE) or 30 (GREEN)
ssh root@10.92.3.XX "cd /opt/quantshift/apps/web && \
  git pull origin main && npm install && npm run build && pm2 restart quantshift-{blue|green}"
```

**Verify deployment:**
```bash
curl -s -o /dev/null -w "%{http_code}" https://quantshift.io
```
