# Disk Management Procedures

**Last Updated:** 2026-02-22  
**Status:** ✅ Tested and Verified

---

## Overview

QuantShift runs on Proxmox LXC containers with LVM-backed storage. This document covers disk expansion, monitoring, and cleanup procedures.

**Current Configuration:**
- **Container Type:** Proxmox LXC (not VMs)
- **Storage Backend:** local-lvm (LVM thin pool)
- **Primary (CT 100):** 26GB rootfs
- **Standby (CT 101):** 26GB rootfs

---

## Disk Expansion Procedure

### Prerequisites
- SSH access to Proxmox host (`root@proxmox`)
- Sufficient free space in LVM pool
- Containers can remain running (online resize)

### Step 1: Check Current Disk Usage

```bash
# From local machine
ssh quantshift-primary "df -h /"
ssh quantshift-standby "df -h /"

# From Proxmox host
ssh root@proxmox "pct list | grep quantshift"
ssh root@proxmox "pct config 100 | grep rootfs"
ssh root@proxmox "pct config 101 | grep rootfs"
```

### Step 2: Check Available Space in LVM Pool

```bash
ssh root@proxmox "pvesm status | grep local-lvm"
```

Example output:
```
local-lvm     lvmthin     active      1793077248       111170789      1681906458    6.20%
```

**Available space:** ~1.6TB free

### Step 3: Expand Container Disk (Online)

```bash
# Expand primary container by 10GB
ssh root@proxmox "pct resize 100 rootfs +10G"

# Expand standby container by 10GB
ssh root@proxmox "pct resize 101 rootfs +10G"
```

**What happens:**
1. LVM logical volume is extended
2. Filesystem is automatically resized (online)
3. No container restart required
4. Changes are immediate

### Step 4: Verify Expansion

```bash
# Check new disk size
ssh quantshift-primary "df -h /"
ssh quantshift-standby "df -h /"

# Verify from Proxmox
ssh root@proxmox "pct config 100 | grep rootfs"
ssh root@proxmox "pct config 101 | grep rootfs"
```

Expected output:
```
Filesystem                        Size  Used Avail Use% Mounted on
/dev/mapper/pve-vm--100--disk--0   26G   14G   12G  54% /
```

---

## Disk Monitoring

### Automated Monitoring (Recommended)

Add to cron on Proxmox host:

```bash
# Check disk usage daily and alert if > 80%
0 6 * * * /usr/local/bin/check-container-disk-usage.sh
```

**Script:** `/usr/local/bin/check-container-disk-usage.sh`
```bash
#!/bin/bash
# Check QuantShift container disk usage

THRESHOLD=80
ADMIN_EMAIL="admin@example.com"

for CT in 100 101; do
    NAME=$(pct config $CT | grep hostname | cut -d: -f2 | tr -d ' ')
    USAGE=$(pct exec $CT -- df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$USAGE" -gt "$THRESHOLD" ]; then
        echo "WARNING: Container $CT ($NAME) disk usage at ${USAGE}%" | \
            mail -s "Disk Alert: $NAME" $ADMIN_EMAIL
    fi
done
```

### Manual Monitoring

```bash
# Quick check from local machine
ssh quantshift-primary "df -h / && du -sh /opt/quantshift/*"
ssh quantshift-standby "df -h / && du -sh /opt/quantshift/*"

# Detailed breakdown
ssh quantshift-primary "du -h --max-depth=1 /opt/quantshift | sort -h"
```

---

## Disk Cleanup Procedures

### 1. Clean System Logs

```bash
# Clean journal logs (keeps last 7 days)
ssh quantshift-primary "sudo journalctl --vacuum-time=7d"
ssh quantshift-standby "sudo journalctl --vacuum-time=7d"

# Clean apt cache
ssh quantshift-primary "sudo apt-get clean && sudo apt-get autoremove -y"
ssh quantshift-standby "sudo apt-get clean && sudo apt-get autoremove -y"
```

**Typical savings:** 1-2GB

### 2. Clean Python Cache

```bash
# Remove __pycache__ directories
ssh quantshift-primary "find /opt/quantshift -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true"
ssh quantshift-standby "find /opt/quantshift -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true"

# Remove .pyc files
ssh quantshift-primary "find /opt/quantshift -name '*.pyc' -delete"
ssh quantshift-standby "find /opt/quantshift -name '*.pyc' -delete"
```

**Typical savings:** 50-100MB

### 3. Clean Old Logs

```bash
# Remove old bot logs (keep last 30 days)
ssh quantshift-primary "find /opt/quantshift/logs -name '*.log' -mtime +30 -delete"
ssh quantshift-standby "find /opt/quantshift/logs -name '*.log' -mtime +30 -delete"

# Remove old training logs (keep last 10)
ssh quantshift-primary "ls -t /opt/quantshift/logs/model-training-*.log | tail -n +11 | xargs -r rm"
```

**Typical savings:** 100-500MB

### 4. Clean Old Model Backups

```bash
# Keep only last 3 model backups (automated by retrain script)
ssh quantshift-primary "ls -t /opt/quantshift/models/backups/*.pkl | tail -n +4 | xargs -r rm"
```

**Typical savings:** 500MB-1GB

### 5. Clean Docker/Container Images (If applicable)

```bash
# Remove unused Docker images
ssh quantshift-primary "docker system prune -a -f"
ssh quantshift-standby "docker system prune -a -f"
```

---

## Disk Space Troubleshooting

### Find Large Files

```bash
# Find files larger than 100MB
ssh quantshift-primary "find /opt/quantshift -type f -size +100M -exec ls -lh {} \;"

# Find largest directories
ssh quantshift-primary "du -h /opt/quantshift | sort -h | tail -20"
```

### Check What's Using Space

```bash
# Breakdown by directory
ssh quantshift-primary "du -sh /opt/quantshift/* | sort -h"

# Typical sizes:
# - venv: 1.4GB (Python packages)
# - apps: 680MB (bot code)
# - logs: 6-40MB (log files)
# - models: 264KB-1GB (ML models + backups)
```

### Emergency Cleanup (If disk full)

```bash
# 1. Clean journals aggressively (keep 1 day)
ssh quantshift-primary "sudo journalctl --vacuum-time=1d"

# 2. Clean all apt cache
ssh quantshift-primary "sudo apt-get clean"

# 3. Remove all old logs
ssh quantshift-primary "rm -f /opt/quantshift/logs/*.log.1 /opt/quantshift/logs/*.log.2*"

# 4. Clear pip cache
ssh quantshift-primary "rm -rf ~/.cache/pip"

# 5. If still critical, expand disk immediately
ssh root@proxmox "pct resize 100 rootfs +5G"
```

---

## Disk Expansion History

| Date | Container | Before | After | Reason |
|------|-----------|--------|-------|--------|
| 2026-02-22 | CT 100 (Primary) | 16GB | 26GB | FinBERT installation (transformers + torch) |
| 2026-02-22 | CT 101 (Standby) | 16GB | 26GB | FinBERT installation (transformers + torch) |

---

## Best Practices

### DO ✅

- **Monitor disk usage weekly** (automated cron job)
- **Expand proactively** when usage > 70%
- **Clean logs regularly** (automated cleanup scripts)
- **Keep model backups** (last 3 versions)
- **Document expansions** (update this file)

### DON'T ❌

- **Don't wait until 95% full** (emergency mode)
- **Don't delete model backups manually** (use automated cleanup)
- **Don't remove venv** (1.4GB but required)
- **Don't clean logs during market hours** (may miss errors)
- **Don't expand without checking LVM pool space**

---

## Container vs VM Commands

**IMPORTANT:** QuantShift uses **LXC containers**, not VMs.

**Correct commands:**
```bash
pct list                    # List containers
pct config 100              # Show container config
pct resize 100 rootfs +10G  # Expand container disk
pct exec 100 -- df -h       # Run command in container
```

**Incorrect commands (for VMs only):**
```bash
qm list                     # ❌ Won't show LXC containers
qm resize 100 scsi0 +10G    # ❌ Wrong command for containers
```

---

## Automation Scripts

### Daily Disk Check Script

**Location:** `/usr/local/bin/check-quantshift-disk.sh`

```bash
#!/bin/bash
# Daily disk usage check for QuantShift containers

THRESHOLD=75
CRITICAL=85

for CT in 100 101; do
    NAME=$(pct config $CT | grep hostname | cut -d: -f2 | tr -d ' ')
    USAGE=$(pct exec $CT -- df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    SIZE=$(pct exec $CT -- df -h / | awk 'NR==2 {print $2}')
    AVAIL=$(pct exec $CT -- df -h / | awk 'NR==2 {print $4}')
    
    echo "[$NAME] Disk: $SIZE, Used: ${USAGE}%, Available: $AVAIL"
    
    if [ "$USAGE" -gt "$CRITICAL" ]; then
        echo "🔴 CRITICAL: $NAME disk at ${USAGE}% - immediate action required!"
    elif [ "$USAGE" -gt "$THRESHOLD" ]; then
        echo "🟡 WARNING: $NAME disk at ${USAGE}% - consider expansion"
    else
        echo "✅ OK: $NAME disk usage healthy"
    fi
done
```

### Weekly Cleanup Script

**Location:** `/usr/local/bin/cleanup-quantshift-disk.sh`

```bash
#!/bin/bash
# Weekly cleanup for QuantShift containers

for CT in 100 101; do
    NAME=$(pct config $CT | grep hostname | cut -d: -f2 | tr -d ' ')
    echo "Cleaning $NAME..."
    
    # Clean journal logs (keep 7 days)
    pct exec $CT -- journalctl --vacuum-time=7d
    
    # Clean Python cache
    pct exec $CT -- find /opt/quantshift -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
    
    # Clean old logs (keep 30 days)
    pct exec $CT -- find /opt/quantshift/logs -name '*.log' -mtime +30 -delete
    
    echo "✅ $NAME cleanup complete"
done
```

---

## Emergency Procedures

### Disk Full - Cannot Start Services

```bash
# 1. Check what's using space
ssh root@proxmox "pct exec 100 -- du -sh /opt/quantshift/* | sort -h"

# 2. Emergency expansion (5GB)
ssh root@proxmox "pct resize 100 rootfs +5G"

# 3. Clean immediately
ssh quantshift-primary "sudo journalctl --vacuum-time=1d && sudo apt-get clean"

# 4. Restart services
ssh quantshift-primary "systemctl restart quantshift-equity quantshift-crypto"
```

### LVM Pool Full

```bash
# Check LVM pool usage
ssh root@proxmox "pvesm status | grep local-lvm"

# If pool is full, need to:
# 1. Clean up other containers
# 2. Expand LVM pool (requires storage admin)
# 3. Migrate to different storage pool
```

---

## References

- **Proxmox LXC Docs:** https://pve.proxmox.com/wiki/Linux_Container
- **LVM Resize Docs:** https://pve.proxmox.com/wiki/Resize_disks
- **Disk Management Best Practices:** Internal wiki

---

## Support

**Questions or issues?**
1. Check disk usage: `df -h /`
2. Check LVM pool space: `pvesm status`
3. Review this document
4. Test expansion in dev environment first
5. Contact infrastructure team for LVM pool issues
