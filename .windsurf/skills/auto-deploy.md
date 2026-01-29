---
name: auto-deploy
description: Automatically deploy code changes during debugging sessions
activation: automatic
---

# Auto-Deploy Skill

## Purpose
Automatically deploy code fixes to containers during active debugging without requiring manual prompts.

## When This Activates

### Automatic Deployment (No Prompt Needed)
When ALL of these conditions are met:
1. Working in an app repo (theoshift, ldc-tools, quantshift)
2. Cascade writes code changes (bug fixes, features)
3. User is in active debugging session

### Actions Taken Automatically
1. ✅ Commit changes with descriptive message
2. ✅ Push to GitHub
3. ✅ SSH deploy to target container:
   - `git pull` - Get latest code
   - `npm install` - Update dependencies
   - `npm run build` - Build application
   - `pm2 restart` - Restart service
4. ✅ Report deployment status
5. ✅ Suggest testing

### Manual Deployment Triggers
User can also trigger deployment by saying:
- "deploy this"
- "test this"
- "test this fix"
- "push and deploy"
- "deploy to standby"

## Container Mapping

**TheoShift:**
- Container: `blue-theoshift` (STANDBY)
- Path: `/opt/theoshift`
- PM2: `theoshift`

**LDC Tools:**
- Container: `ldc-staging` (STANDBY)
- Path: `/opt/ldc-tools/frontend`
- PM2: `ldc-tools`

**QuantShift:**
- Container: `qs-dashboard`
- Path: `/opt/quantshift`
- PM2: `quantshift-dashboard`

## Safety

**Git commits provide audit trail:**
- Every deployment = git commit
- Commit message includes "auto-deployed during debugging"
- Can revert any change: `git revert HEAD`
- Can reset to previous state: `git reset --hard HEAD~1`

**Deployment only to STANDBY:**
- Never deploys to LIVE automatically
- STANDBY is safe testing environment
- Traffic switch requires explicit /release workflow

## Debugging Mode

**Enable auto-deploy for session:**
```bash
# In app repo root
touch .debugging
```

**Disable auto-deploy:**
```bash
rm .debugging
```

**When enabled:**
- Every code change triggers automatic deployment
- No manual prompts needed
- Fast iteration during debugging

**When disabled:**
- Cascade suggests deployment after code changes
- User must say "deploy this" to trigger
- More control, less automation

## Example Workflow

### With Auto-Deploy Enabled
```
You: "Fix the 404 error on /api/users"
Cascade: [Investigates, finds bug, implements fix]
Cascade: 🚀 Auto-deploying to blue-theoshift...
         ✅ Changes committed
         ✅ Pushed to GitHub
         ✅ Deployed to blue-theoshift
         💡 Test your changes now
You: [Tests immediately]
```

### With Auto-Deploy Disabled
```
You: "Fix the 404 error on /api/users"
Cascade: [Investigates, finds bug, implements fix]
Cascade: 💡 Code changes ready. Say 'deploy this' to test.
You: "deploy this"
Cascade: 🚀 Deploying to blue-theoshift...
         ✅ Deployed
         💡 Test your changes now
```

## Rollback

**If deployment breaks something:**
```
You: "Revert the last change"
Cascade: git revert HEAD
         git push origin main
         [SSH deploys reverted code]
         ✅ Reverted to previous working state
```

## Notes

- Auto-deploy only works in app repos (not control plane)
- Requires SSH access to containers
- Requires git remote configured
- PM2 must be running on containers
- Uses STANDBY containers only (safe for testing)
