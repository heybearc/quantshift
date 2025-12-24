# CI/CD Pipeline Documentation

## Overview

Automated CI/CD pipeline using GitHub Actions for testing, deployment, and rollback of the QuantShift trading system.

## Pipeline Stages

### 1. Continuous Integration (CI)

**Triggered on:** Push to `main` or `develop`, Pull Requests to `main`

**Python Testing:**
- Install core package and bot packages
- Run unit tests with pytest
- Type checking with mypy
- Code coverage reporting

**Dashboard Testing:**
- Install Node.js dependencies
- Run ESLint linting
- Build Next.js application
- Verify no build errors

### 2. Continuous Deployment (CD)

**Triggered on:** Push to `main` branch (after tests pass)

**Deployment Order:**
1. **Standby First (Canary)** - LXC 101
   - Deploy to standby container
   - Wait 30 seconds for stabilization
   - Verify health checks
   - If fails, stop deployment

2. **Primary Second** - LXC 100
   - Deploy to primary container
   - Wait 30 seconds for stabilization
   - Verify health checks
   - If fails, automatic rollback

3. **Dashboard** - LXC 137
   - Deploy dashboard separately
   - Build and reload with PM2
   - Zero-downtime deployment

## Canary Deployment Strategy

### Why Standby First?

1. **Risk Mitigation:** Test new code on standby before primary
2. **Zero Downtime:** Primary continues running during standby deployment
3. **Quick Rollback:** If standby fails, primary is unaffected
4. **Gradual Rollout:** Validate changes before full deployment

### Deployment Flow

```
┌─────────────────────────────────────────────────────────┐
│ 1. Tests Pass                                           │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Deploy to Standby (LXC 101)                         │
│    - git pull                                           │
│    - systemctl restart quantshift-equity                │
│    - Wait 30s                                           │
│    - Health check                                       │
└─────────────────────────────────────────────────────────┘
                        ↓
                   ✅ Success?
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Deploy to Primary (LXC 100)                         │
│    - git pull                                           │
│    - systemctl restart quantshift-equity                │
│    - Wait 30s                                           │
│    - Health check                                       │
└─────────────────────────────────────────────────────────┘
                        ↓
                   ✅ Success?
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Deploy Dashboard (LXC 137)                          │
│    - git pull                                           │
│    - npm install && npm run build                       │
│    - pm2 reload quantshift-dashboard                    │
└─────────────────────────────────────────────────────────┘
```

## Rollback Automation

### Manual Rollback

Trigger via GitHub Actions UI:
1. Go to Actions → Rollback Deployment
2. Select target (primary/standby/both/dashboard)
3. Specify number of commits to rollback
4. Run workflow

### Automatic Rollback

If health checks fail after deployment:
- Automatically rollback to previous commit
- Restart services
- Send notification

### Rollback Commands

```bash
# Rollback primary
ssh quantshift-primary 'cd /opt/quantshift && git reset --hard HEAD~1 && systemctl restart quantshift-equity'

# Rollback standby
ssh quantshift-standby 'cd /opt/quantshift && git reset --hard HEAD~1 && systemctl restart quantshift-equity'

# Rollback dashboard
ssh quantshift-dashboard 'cd /opt/quantshift && git reset --hard HEAD~1 && cd apps/dashboard && npm run build && pm2 reload quantshift-dashboard'
```

## Health Checks

### Bot Health Check
```bash
# Check service status
systemctl status quantshift-equity

# Check logs for errors
journalctl -u quantshift-equity -n 50 --no-pager | grep -i error

# Check Redis heartbeat
redis-cli -a Cloudy_92! GET "bot:equity-bot:heartbeat"

# Check if bot is primary
redis-cli -a Cloudy_92! GET "bot:equity-bot:primary_lock"
```

### Dashboard Health Check
```bash
# Check PM2 status
pm2 status quantshift-dashboard

# Check if responding
curl -I http://10.92.3.29:3000

# Check logs
pm2 logs quantshift-dashboard --lines 50
```

## GitHub Secrets Required

For full automation (when ready to enable SSH):

```
DEPLOY_SSH_KEY - SSH private key for container access
PRIMARY_HOST - 10.92.3.27
STANDBY_HOST - 10.92.3.28
DASHBOARD_HOST - 10.92.3.29
```

## Current Status

**Phase 1: Manual Deployment** ✅
- GitHub Actions workflows created
- Tests run automatically
- Deployment commands documented
- Manual SSH deployment required

**Phase 2: Automated Deployment** (Future)
- Add SSH keys to GitHub Secrets
- Enable automated SSH deployment
- Add Slack/Discord notifications
- Implement automatic rollback on failure

## Usage

### Triggering Deployment

```bash
# Make changes
git add .
git commit -m "feat: your changes"
git push origin main

# GitHub Actions will:
# 1. Run tests
# 2. Deploy to standby (manual for now)
# 3. Deploy to primary (manual for now)
# 4. Deploy dashboard (manual for now)
```

### Manual Deployment (Current)

```bash
# Deploy bots (hot-standby)
./infrastructure/deployment/deploy-bots.sh

# Deploy dashboard
./infrastructure/deployment/deploy-dashboard.sh
```

### Monitoring Deployment

```bash
# Watch GitHub Actions
open https://github.com/heybearc/quantshift/actions

# Check bot status
ssh quantshift-primary 'systemctl status quantshift-equity'
ssh quantshift-standby 'systemctl status quantshift-equity'

# Check dashboard
ssh quantshift-dashboard 'pm2 status'
```

## Best Practices

1. **Always test locally first** before pushing to main
2. **Use feature branches** for development
3. **Create pull requests** for code review
4. **Monitor logs** after deployment
5. **Keep standby in sync** with primary
6. **Test rollback** periodically
7. **Document changes** in commit messages

## Troubleshooting

### Deployment Fails

1. Check GitHub Actions logs
2. SSH to container and check logs
3. Verify git pull succeeded
4. Check service status
5. Review recent commits

### Health Check Fails

1. Check systemctl status
2. Review application logs
3. Verify Redis connection
4. Check PostgreSQL connection
5. Verify API keys are valid

### Rollback Needed

1. Trigger rollback workflow
2. Or manually SSH and rollback
3. Verify services restart
4. Check logs for errors
5. Monitor for stability

## Future Enhancements

- [ ] Add automated integration tests
- [ ] Implement blue-green deployment for dashboard
- [ ] Add performance benchmarking
- [ ] Implement gradual traffic shifting
- [ ] Add automated smoke tests
- [ ] Integrate with monitoring (Grafana)
- [ ] Add deployment notifications (Slack/Discord)
- [ ] Implement feature flags
