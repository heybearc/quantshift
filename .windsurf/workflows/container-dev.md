---
description: Container-based development workflow - NO local Mac development allowed
---

# QuantShift Container Development Workflow

## 🚨 CRITICAL: Development Location Check

**Before ANY development work, verify you are on the correct container:**

```bash
# Check hostname
hostname

# Expected results:
# - quantshift-admin (LXC 137) for admin-web work
# - quantshift-bot-primary (LXC 100) for equity bot work
# - quantshift-bot-standby (LXC 101) for equity bot work
```

**If you are on your Mac (`/Users/cory/...`), STOP IMMEDIATELY.**

---

## 📍 Container Assignments

### Admin Web Development
```bash
# SSH to admin container
ssh root@10.92.3.29

# Navigate to project
cd /opt/quantshift/apps/admin-web

# Verify location
pwd  # Should show: /opt/quantshift/apps/admin-web
```

### Equity Bot Development
```bash
# SSH to primary bot container
ssh root@10.92.3.27

# Navigate to project
cd /opt/quantshift/apps/bots/equity

# Verify location
pwd  # Should show: /opt/quantshift/apps/bots/equity
```

---

## 🔄 Standard Development Flow

### 1. Pre-Flight Checks
```bash
# Verify you're on container (NOT Mac)
hostname

# Pull latest code
git pull origin main

# Check service status
systemctl status quantshift-admin  # or quantshift-equity-bot
```

### 2. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 3. Develop on Container
```bash
# Make your changes using vim/nano or remote editor
# For admin-web:
npm install  # if dependencies changed
npx prisma generate  # if schema changed
npm run build  # test build

# For equity bot:
source venv/bin/activate
pip install -r requirements.txt  # if dependencies changed
python run_bot.py  # test bot
```

### 4. Test on Container
```bash
# Restart service
systemctl restart quantshift-admin  # or quantshift-equity-bot

# Check logs
journalctl -u quantshift-admin -f  # or quantshift-equity-bot

# Verify functionality
curl http://localhost:3001  # for admin-web
```

### 5. Commit and Push
```bash
git add .
git commit -m "feat(component): Description of changes"
git push origin feature/your-feature-name
```

### 6. Merge to Main
```bash
git checkout main
git merge feature/your-feature-name
git push origin main
```

### 7. Sync to Standby (If Bot Work)
```bash
# If you modified equity bot, sync to standby
ssh root@10.92.3.28
cd /opt/quantshift
git pull origin main
cd apps/bots/equity
source venv/bin/activate
pip install -r requirements.txt
systemctl restart quantshift-equity-bot
```

---

## 🚫 PROHIBITED: Local Mac Development

**NEVER develop in:**
- `/Users/cory/Documents/Cloudy-Work/applications/quantshift`

**If you find yourself there, STOP and SSH to the correct container.**

---

## ✅ Quick Reference

| Component | Container | IP | SSH Command |
|-----------|-----------|----|----|
| Admin Web | LXC 137 | 10.92.3.29 | `ssh root@10.92.3.29` |
| Bot Primary | LXC 100 | 10.92.3.27 | `ssh root@10.92.3.27` |
| Bot Standby | LXC 101 | 10.92.3.28 | `ssh root@10.92.3.28` |
| Database | LXC 131 | 10.92.3.21 | `psql -h 10.92.3.21 -U quantshift` |

---

## 🔧 Remote Development Setup

### VS Code Remote SSH
1. Install "Remote - SSH" extension
2. Add to `~/.ssh/config`:
   ```
   Host quantshift-admin
       HostName 10.92.3.29
       User root
   
   Host quantshift-bot-primary
       HostName 10.92.3.27
       User root
   
   Host quantshift-bot-standby
       HostName 10.92.3.28
       User root
   ```
3. Connect: Command Palette → "Remote-SSH: Connect to Host"
4. Open folder: `/opt/quantshift`

---

**This workflow is MANDATORY and IMMUTABLE. No exceptions.**
