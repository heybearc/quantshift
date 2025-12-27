# QuantShift Container-Based Development Workflow

## 🚨 IMMUTABLE RULE: NO LOCAL MAC DEVELOPMENT

**ALL development work MUST be performed directly on the target LXC container where the code will run.**

This document defines the mandatory development workflow to prevent confusion, deployment issues, and ensure code consistency.

---

## 📍 Container Assignments

### **Admin Web Application (admin-web)**
- **Target Container**: LXC 137 (10.92.3.29)
- **SSH Access**: `ssh root@10.92.3.29`
- **Working Directory**: `/opt/quantshift/apps/admin-web`
- **Service Name**: `quantshift-admin`
- **Port**: 3001
- **Technology**: Next.js 14, TypeScript, Prisma, PostgreSQL

### **Equity Bot (Primary)**
- **Target Container**: LXC 100 (10.92.3.27)
- **SSH Access**: `ssh root@10.92.3.27`
- **Working Directory**: `/opt/quantshift/apps/bots/equity`
- **Service Name**: `quantshift-equity-bot`
- **Technology**: Python 3.11+, Alpaca API

### **Equity Bot (Standby)**
- **Target Container**: LXC 101 (10.92.3.28)
- **SSH Access**: `ssh root@10.92.3.28`
- **Working Directory**: `/opt/quantshift/apps/bots/equity`
- **Service Name**: `quantshift-equity-bot`
- **Technology**: Python 3.11+, Alpaca API
- **Note**: Must stay in sync with Primary (LXC 100)

### **Shared Database**
- **Container**: LXC 131 (10.92.3.21)
- **Access**: `psql -h 10.92.3.21 -U quantshift -d quantshift`
- **Technology**: PostgreSQL 15

---

## 🔄 Development Workflow

### **Step 1: Identify Target Container**

Before ANY development work:

1. **Determine which component you're modifying:**
   - Admin web features → LXC 137
   - Equity bot logic → LXC 100 (then sync to LXC 101)
   - Database schema → Run migrations from LXC 137

2. **SSH to the correct container:**
   ```bash
   # Admin web
   ssh root@10.92.3.29
   
   # Equity bot primary
   ssh root@10.92.3.27
   
   # Equity bot standby
   ssh root@10.92.3.28
   ```

### **Step 2: Navigate to Working Directory**

```bash
cd /opt/quantshift
```

### **Step 3: Create Feature Branch**

```bash
# Pull latest
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
```

### **Step 4: Develop ON THE CONTAINER**

**For Admin Web (LXC 137):**
```bash
cd /opt/quantshift/apps/admin-web

# Make your changes using vim/nano or remote editing
# Install dependencies if needed
npm install

# Run Prisma commands if schema changed
npx prisma generate
npx prisma db push  # or migrate dev

# Test build
npm run build

# Restart service to test
systemctl restart quantshift-admin

# Check logs
journalctl -u quantshift-admin -f
```

**For Equity Bot (LXC 100):**
```bash
cd /opt/quantshift/apps/bots/equity

# Activate virtual environment
source venv/bin/activate

# Make your changes
# Install dependencies if needed
pip install -r requirements.txt

# Test the bot
python run_bot.py

# If good, restart service
systemctl restart quantshift-equity-bot

# Check logs
journalctl -u quantshift-equity-bot -f
```

### **Step 5: Commit and Push**

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat(admin): Add session management page

- Created session management UI
- Added API endpoints for session tracking
- Implemented session termination
"

# Push to GitHub
git push origin feature/your-feature-name
```

### **Step 6: Merge to Main**

```bash
# Switch to main
git checkout main

# Merge feature branch
git merge feature/your-feature-name

# Push to main
git push origin main

# Delete feature branch
git branch -d feature/your-feature-name
```

### **Step 7: Sync to Other Containers (If Needed)**

**If you modified equity bot on LXC 100, sync to LXC 101:**
```bash
# SSH to standby
ssh root@10.92.3.28

# Pull latest
cd /opt/quantshift
git pull origin main

# Rebuild if needed
cd apps/bots/equity
source venv/bin/activate
pip install -r requirements.txt

# Restart service
systemctl restart quantshift-equity-bot
```

---

## 🚫 PROHIBITED ACTIONS

### **NEVER DO THESE:**

1. ❌ **NO development on local Mac** (`/Users/cory/Documents/Cloudy-Work/applications/quantshift`)
2. ❌ **NO building locally then deploying**
3. ❌ **NO copying files from Mac to container**
4. ❌ **NO "I'll just test it locally first"**
5. ❌ **NO committing from Mac**

### **Why These Are Prohibited:**

- **Environment Differences**: Mac ≠ Linux container (different paths, permissions, dependencies)
- **Deployment Confusion**: "Did I deploy the latest?" becomes impossible to answer
- **Schema Mismatches**: Local database ≠ production database
- **Wasted Time**: Building twice, debugging environment differences
- **Version Drift**: Code on Mac diverges from container code

---

## ✅ MANDATORY PRE-FLIGHT CHECKS

Before starting ANY development work, verify:

### **Check 1: Am I on the correct container?**
```bash
hostname
# Should return: quantshift-admin (LXC 137) or similar
```

### **Check 2: Am I in the correct directory?**
```bash
pwd
# Should return: /opt/quantshift/apps/admin-web or /opt/quantshift/apps/bots/equity
```

### **Check 3: Is the repository up to date?**
```bash
git status
git pull origin main
```

### **Check 4: Is the service running?**
```bash
systemctl status quantshift-admin  # or quantshift-equity-bot
```

---

## 🔧 Remote Development Tools

### **Option 1: SSH + Vim/Nano**
```bash
ssh root@10.92.3.29
cd /opt/quantshift/apps/admin-web
vim app/admin/sessions/page.tsx
```

### **Option 2: VS Code Remote SSH**
1. Install "Remote - SSH" extension
2. Add SSH config:
   ```
   Host quantshift-admin
       HostName 10.92.3.29
       User root
   ```
3. Connect via Command Palette: "Remote-SSH: Connect to Host"
4. Open folder: `/opt/quantshift/apps/admin-web`

### **Option 3: Windsurf Remote Development**
- Use Windsurf's remote development features
- Connect directly to container
- Full AI assistance while developing on container

---

## 📊 Verification Commands

### **Admin Web (LXC 137)**
```bash
# Check service status
systemctl status quantshift-admin

# Check logs
journalctl -u quantshift-admin -n 50

# Check port
curl http://localhost:3001

# Check database connection
cd /opt/quantshift/apps/admin-web
npx prisma db pull

# Check build
npm run build
```

### **Equity Bot (LXC 100/101)**
```bash
# Check service status
systemctl status quantshift-equity-bot

# Check logs
journalctl -u quantshift-equity-bot -n 50

# Check Python environment
source venv/bin/activate
python --version
pip list | grep alpaca

# Test bot connection
python -c "from alpaca.trading.client import TradingClient; print('OK')"
```

---

## 🔄 Hot-Standby Sync Process

When modifying equity bot code:

### **Step 1: Develop on Primary (LXC 100)**
```bash
ssh root@10.92.3.27
cd /opt/quantshift
# Make changes, test, commit, push
```

### **Step 2: Sync to Standby (LXC 101)**
```bash
ssh root@10.92.3.28
cd /opt/quantshift
git pull origin main
cd apps/bots/equity
source venv/bin/activate
pip install -r requirements.txt
systemctl restart quantshift-equity-bot
```

### **Step 3: Verify Both Running**
```bash
# Check primary
ssh root@10.92.3.27 'systemctl status quantshift-equity-bot'

# Check standby
ssh root@10.92.3.28 'systemctl status quantshift-equity-bot'
```

---

## 🎯 Workflow Summary

```
┌─────────────────────────────────────────────────────────────┐
│  IDENTIFY COMPONENT → SSH TO CONTAINER → DEVELOP ON CONTAINER │
│  → TEST ON CONTAINER → COMMIT → PUSH → SYNC IF NEEDED       │
└─────────────────────────────────────────────────────────────┘
```

### **Example: Adding a New Admin Feature**

```bash
# 1. SSH to admin container
ssh root@10.92.3.29

# 2. Navigate to project
cd /opt/quantshift/apps/admin-web

# 3. Pull latest
git pull origin main

# 4. Create feature branch
git checkout -b feature/audit-logs

# 5. Make changes (using vim or remote editor)
vim app/admin/audit-logs/page.tsx

# 6. Test build
npm run build

# 7. Restart service
systemctl restart quantshift-admin

# 8. Verify in browser
curl http://localhost:3001/admin/audit-logs

# 9. Commit
git add .
git commit -m "feat(admin): Add audit logs viewer"

# 10. Push
git push origin feature/audit-logs

# 11. Merge to main
git checkout main
git merge feature/audit-logs
git push origin main
```

---

## 🚨 Emergency Rollback

If something breaks:

```bash
# SSH to affected container
ssh root@10.92.3.29  # or 10.92.3.27/28

# Navigate to project
cd /opt/quantshift

# Check git log
git log --oneline -10

# Rollback to previous commit
git reset --hard <commit-hash>

# Rebuild if needed
cd apps/admin-web && npm run build  # or apps/bots/equity

# Restart service
systemctl restart quantshift-admin  # or quantshift-equity-bot

# Verify
systemctl status quantshift-admin
```

---

## 📝 Commit Message Standards

Follow conventional commits:

```
feat(admin): Add new feature
fix(bot): Fix bug in strategy
docs(readme): Update documentation
refactor(api): Refactor API endpoint
test(bot): Add unit tests
chore(deps): Update dependencies
```

---

## 🎉 Success Criteria

You're following the workflow correctly when:

- ✅ All development happens via SSH to target container
- ✅ No local Mac development directory is touched
- ✅ Git commits are made from the container
- ✅ Services are tested on the container before pushing
- ✅ Hot-standby containers stay in sync
- ✅ No "deployment" step needed (code runs where it's developed)

---

## 🔒 Enforcement

This workflow is **IMMUTABLE** and **MANDATORY**. Any deviation will cause:
- Deployment confusion
- Environment mismatches
- Wasted debugging time
- Version control issues

**If you find yourself on your Mac working in `/Users/cory/Documents/Cloudy-Work/applications/quantshift`, STOP IMMEDIATELY and SSH to the correct container.**

---

**Last Updated**: 2025-12-27
**Status**: ACTIVE AND ENFORCED
