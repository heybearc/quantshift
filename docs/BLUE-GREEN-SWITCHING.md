# Blue-Green Switching Runbook for QuantShift

**Date:** 2026-01-26  
**Purpose:** Step-by-step guide for switching between blue and green environments

---

## Infrastructure Overview

| Component | Hostname | IP | Port | Purpose |
|-----------|----------|-----|------|---------|
| **Blue** | quantshift-blue | 10.92.3.29 | 3001 | Blue environment |
| **Green** | quantshift-green | 10.92.3.30 | 3001 | Green environment |
| **HAProxy** | haproxy | 10.92.3.26 | 80 | Load balancer |
| **PostgreSQL** | postgresql | 10.92.3.21 | 5432 | Shared database |

**Current LIVE:** Blue (10.92.3.29)  
**Current STANDBY:** Green (10.92.3.30)

---

## Pre-Deployment Checklist

Before switching environments, verify:

- [ ] New code deployed to STANDBY environment
- [ ] STANDBY environment built successfully (`npm run build`)
- [ ] STANDBY PM2 process is online
- [ ] Database migrations run (if needed)
- [ ] Health check passes on STANDBY
- [ ] Smoke tests pass on STANDBY
- [ ] No active user sessions (or acceptable to interrupt)

---

## Switching from Blue to Green

### Step 1: Verify STANDBY (Green) is Healthy

```bash
# Check PM2 status
ssh root@10.92.3.30 "pm2 status"

# Check application responds
curl -I http://10.92.3.30:3001

# Check through HAProxy
curl -I http://10.92.3.26 -H "Host: quantshift.io"

# Expected: HTTP 200
```

### Step 2: Backup Current HAProxy Config

```bash
ssh root@10.92.3.26 "cp /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.backup-$(date +%Y%m%d-%H%M)"
```

### Step 3: Update HAProxy to Route to Green

```bash
# Edit HAProxy config
ssh root@10.92.3.26 "sed -i 's|server blue 10.92.3.29:3001|server green 10.92.3.30:3001|' /etc/haproxy/haproxy.cfg"

# Verify syntax
ssh root@10.92.3.26 "haproxy -c -f /etc/haproxy/haproxy.cfg"

# Reload HAProxy (zero downtime)
ssh root@10.92.3.26 "systemctl reload haproxy"
```

### Step 4: Verify Traffic is Routing to Green

```bash
# Test via HAProxy
curl -I https://trader.cloudigan.net

# Check HAProxy stats
ssh root@10.92.3.26 "echo 'show stat' | socat stdio /run/haproxy/admin.sock | grep quantshift"

# Verify green is receiving traffic
ssh root@10.92.3.30 "pm2 logs quantshift-admin --lines 10 --nostream"
```

### Step 5: Monitor for Issues

**Watch for:**
- 500/502/503 errors
- Slow response times
- Database connection errors
- PM2 restarts

**Monitoring commands:**
```bash
# Watch HAProxy logs
ssh root@10.92.3.26 "tail -f /var/log/haproxy.log"

# Watch PM2 logs
ssh root@10.92.3.30 "pm2 logs quantshift-admin"

# Check error rate
curl -I https://trader.cloudigan.net
```

### Step 6: Rollback if Needed

If issues occur, immediately switch back to blue:

```bash
# Restore backup config
ssh root@10.92.3.26 "cp /etc/haproxy/haproxy.cfg.backup-* /etc/haproxy/haproxy.cfg"

# OR manually switch back
ssh root@10.92.3.26 "sed -i 's|server green 10.92.3.30:3001|server blue 10.92.3.29:3001|' /etc/haproxy/haproxy.cfg"

# Reload
ssh root@10.92.3.26 "haproxy -c -f /etc/haproxy/haproxy.cfg && systemctl reload haproxy"
```

---

## Switching from Green to Blue

Same process, but reverse the IPs:

```bash
# Switch to blue
ssh root@10.92.3.26 "sed -i 's|server green 10.92.3.30:3001|server blue 10.92.3.29:3001|' /etc/haproxy/haproxy.cfg"

# Validate and reload
ssh root@10.92.3.26 "haproxy -c -f /etc/haproxy/haproxy.cfg && systemctl reload haproxy"
```

---

## Deployment Workflow

### Typical Blue-Green Deployment

**Scenario:** Blue is LIVE, deploying new version to Green

1. **Deploy to STANDBY (Green):**
   ```bash
   ssh root@10.92.3.30 "cd /opt/quantshift && git pull origin main"
   ssh root@10.92.3.30 "cd /opt/quantshift/apps/web && npm install && npm run build"
   ssh root@10.92.3.30 "pm2 restart quantshift-admin"
   ```

2. **Test STANDBY:**
   ```bash
   curl -I http://10.92.3.30:3001
   # Run smoke tests
   ```

3. **Switch traffic to Green:**
   ```bash
   # Follow "Switching from Blue to Green" steps above
   ```

4. **Monitor Green (now LIVE):**
   ```bash
   # Watch for 5-10 minutes
   ssh root@10.92.3.30 "pm2 logs quantshift-admin"
   ```

5. **Update Blue (now STANDBY) with same code:**
   ```bash
   ssh root@10.92.3.29 "cd /opt/quantshift && git pull origin main"
   ssh root@10.92.3.29 "cd /opt/quantshift/apps/web && npm install && npm run build"
   ssh root@10.92.3.29 "pm2 restart quantshift-admin"
   ```

6. **Both environments now in sync** - Ready for next deployment

---

## Quick Reference Commands

### Check Current LIVE Environment

```bash
# Check HAProxy config
ssh root@10.92.3.26 "grep 'server.*10.92.3' /etc/haproxy/haproxy.cfg | grep trader_backend"

# If shows 10.92.3.29 → Blue is LIVE
# If shows 10.92.3.30 → Green is LIVE
```

### Health Check Commands

```bash
# Blue health
curl -I http://10.92.3.29:3001

# Green health
curl -I http://10.92.3.30:3001

# HAProxy health
curl -I http://10.92.3.26 -H "Host: quantshift.io"

# Production health
curl -I https://trader.cloudigan.net
```

### Emergency Rollback

```bash
# Restore last backup
ssh root@10.92.3.26 "cp /etc/haproxy/haproxy.cfg.backup-before-blue-green /etc/haproxy/haproxy.cfg && systemctl reload haproxy"
```

---

## Troubleshooting

### Issue: 502 Bad Gateway after switch

**Cause:** STANDBY environment not healthy  
**Fix:**
```bash
# Check PM2 status
ssh root@10.92.3.30 "pm2 status"

# Restart if needed
ssh root@10.92.3.30 "pm2 restart quantshift-admin"

# Check logs
ssh root@10.92.3.30 "pm2 logs quantshift-admin --lines 50"
```

### Issue: Database connection errors

**Cause:** Database migrations not run  
**Fix:**
```bash
ssh root@10.92.3.30 "cd /opt/quantshift/apps/web && npx prisma migrate deploy"
```

### Issue: Old code still showing

**Cause:** Browser cache or CDN cache  
**Fix:**
- Hard refresh browser (Cmd+Shift+R)
- Clear browser cache
- Wait for CDN cache to expire

---

## Best Practices

1. **Always test STANDBY before switching**
2. **Deploy during low-traffic periods**
3. **Monitor for 5-10 minutes after switch**
4. **Keep both environments in sync**
5. **Document each deployment**
6. **Have rollback plan ready**
7. **Communicate with users about maintenance windows**

---

## Automation Opportunities

Future enhancements:
- Script to automate HAProxy switch
- Health check validation before switch
- Automated rollback on error detection
- Slack/email notifications on switch
- Integration with `/bump` workflow

---

## Notes

- **Zero downtime:** HAProxy reload is seamless
- **Session persistence:** Users may need to re-login after switch
- **Database shared:** No data migration needed
- **Both environments:** Always keep in sync for quick rollback
