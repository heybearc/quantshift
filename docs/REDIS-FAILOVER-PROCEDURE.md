# Redis Failover Procedure

**Last Updated:** 2026-02-25  
**Purpose:** Document how to manually or automatically failover Redis from primary to standby

---

## Architecture

### Current Setup
- **Primary Redis:** CT 100 (10.92.3.27:6379) - MASTER
- **Standby Redis:** CT 101 (10.92.3.28:6379) - SLAVE
- **Replication:** Master → Slave (real-time sync)
- **Configuration:**
  - maxmemory: 512 MB
  - maxmemory-policy: allkeys-lru
  - RDB snapshots: every 15 min (save 900 1)

### Replication Status
```bash
# Check on standby
ssh quantshift-standby "redis-cli INFO replication"

# Should show:
# role:slave
# master_host:10.92.3.27
# master_link_status:up
```

---

## Manual Failover Procedure

### Scenario 1: Primary Redis Down (Emergency)

**Steps:**
```bash
# 1. Promote standby to master
ssh quantshift-standby "redis-cli SLAVEOF NO ONE"

# 2. Verify promotion
ssh quantshift-standby "redis-cli INFO replication | grep role"
# Should show: role:master

# 3. Update bot configuration to use standby Redis
# (Bots should automatically reconnect)

# 4. Restart bots if needed
ssh quantshift-standby "systemctl restart quantshift-equity quantshift-crypto"
```

**Expected Downtime:** < 30 seconds

### Scenario 2: Planned Maintenance (Graceful)

**Steps:**
```bash
# 1. Stop primary bots
ssh quantshift-primary "systemctl stop quantshift-equity quantshift-crypto"

# 2. Wait for replication to catch up (check lag)
ssh quantshift-standby "redis-cli INFO replication | grep slave_repl_offset"

# 3. Promote standby to master
ssh quantshift-standby "redis-cli SLAVEOF NO ONE"

# 4. Start standby bots
ssh quantshift-standby "systemctl start quantshift-equity quantshift-crypto"

# 5. Perform maintenance on primary

# 6. When ready, make primary the new slave
ssh quantshift-primary "redis-cli SLAVEOF 10.92.3.28 6379"
ssh quantshift-primary "redis-cli CONFIG SET masterauth 'Cloudy_92!'"
```

**Expected Downtime:** 0 seconds (graceful handoff)

---

## Automated Failover (Future)

### Failover Monitor Script
Location: `/opt/quantshift/scripts/failover_monitor.py` (to be created)

**Logic:**
```python
while True:
    # Check primary bot heartbeat
    primary_heartbeat = db.get_heartbeat('quantshift-equity')
    
    if time.now() - primary_heartbeat > 60:
        # Primary is down
        logger.critical("Primary bot down, initiating failover")
        
        # Promote standby Redis
        subprocess.run(['redis-cli', 'SLAVEOF', 'NO', 'ONE'])
        
        # Start standby bots
        subprocess.run(['systemctl', 'start', 'quantshift-equity'])
        subprocess.run(['systemctl', 'start', 'quantshift-crypto'])
        
        # Update database status
        db.set_status('quantshift-equity', 'PRIMARY')
        
        # Send alert
        send_alert("Failover completed: Standby is now PRIMARY")
        
    sleep(10)
```

**Systemd Service:**
```ini
[Unit]
Description=QuantShift Redis Failover Monitor
After=network.target redis.service

[Service]
Type=simple
ExecStart=/opt/quantshift/venv/bin/python /opt/quantshift/scripts/failover_monitor.py
Restart=always
RestartSec=10s
User=quantshift

[Install]
WantedBy=multi-user.target
```

---

## Failback Procedure

### Return to Primary After Recovery

**Steps:**
```bash
# 1. Verify primary Redis is healthy
ssh quantshift-primary "redis-cli PING"

# 2. Make primary a slave of standby (to sync data)
ssh quantshift-primary "redis-cli SLAVEOF 10.92.3.28 6379"
ssh quantshift-primary "redis-cli CONFIG SET masterauth 'Cloudy_92!'"

# 3. Wait for full sync
ssh quantshift-primary "redis-cli INFO replication | grep master_link_status"
# Should show: master_link_status:up

# 4. Stop standby bots
ssh quantshift-standby "systemctl stop quantshift-equity quantshift-crypto"

# 5. Promote primary back to master
ssh quantshift-primary "redis-cli SLAVEOF NO ONE"

# 6. Make standby a slave again
ssh quantshift-standby "redis-cli SLAVEOF 10.92.3.27 6379"

# 7. Start primary bots
ssh quantshift-primary "systemctl start quantshift-equity quantshift-crypto"
```

---

## Testing Failover

### Test 1: Simulate Primary Failure
```bash
# 1. Stop primary Redis
ssh quantshift-primary "systemctl stop redis"

# 2. Promote standby
ssh quantshift-standby "redis-cli SLAVEOF NO ONE"

# 3. Verify standby is master
ssh quantshift-standby "redis-cli INFO replication | grep role"

# 4. Restore primary
ssh quantshift-primary "systemctl start redis"
ssh quantshift-primary "redis-cli SLAVEOF 10.92.3.28 6379"
```

### Test 2: Measure Failover Time
```bash
# Use this script to measure end-to-end failover time
time {
    ssh quantshift-standby "redis-cli SLAVEOF NO ONE"
    ssh quantshift-standby "systemctl start quantshift-equity"
}

# Target: < 30 seconds
```

---

## Monitoring

### Key Metrics to Watch
- **Replication Lag:** `slave_repl_offset` vs `master_repl_offset`
- **Master Link Status:** Should be "up"
- **Last IO:** Should be < 5 seconds
- **Memory Usage:** Should be < 512 MB

### Prometheus Alerts
```yaml
- alert: RedisReplicationDown
  expr: redis_master_link_down == 1
  for: 1m
  annotations:
    summary: "Redis replication is down"
    
- alert: RedisReplicationLag
  expr: redis_slave_repl_offset - redis_master_repl_offset > 1000000
  for: 5m
  annotations:
    summary: "Redis replication lag is high"
```

---

## Troubleshooting

### Issue: Replication Not Working
```bash
# Check master config
ssh quantshift-primary "redis-cli CONFIG GET requirepass"

# Check slave config
ssh quantshift-standby "redis-cli CONFIG GET masterauth"

# Verify network connectivity
ssh quantshift-standby "telnet 10.92.3.27 6379"
```

### Issue: Failover Doesn't Start Bots
```bash
# Check systemd status
ssh quantshift-standby "systemctl status quantshift-equity"

# Check logs
ssh quantshift-standby "journalctl -u quantshift-equity -n 50"
```

### Issue: Data Loss After Failover
```bash
# Check RDB snapshot
ssh quantshift-primary "ls -lh /var/lib/redis/dump.rdb"

# Restore from snapshot if needed
ssh quantshift-standby "redis-cli SHUTDOWN SAVE"
ssh quantshift-standby "cp /var/lib/redis/dump.rdb /var/lib/redis/dump.rdb.backup"
```
