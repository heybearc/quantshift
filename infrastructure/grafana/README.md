# QuantShift Grafana Dashboards

## Quick Import Instructions

### Access Grafana
- URL: http://grafana.cloudigan.net
- Username: `admin`
- Password: `Cloudy_92!`

### Import Dashboards

1. **Navigate to Dashboards**
   - Click the "+" icon in the left sidebar
   - Select "Import"

2. **Import System Health Dashboard**
   - Click "Upload JSON file"
   - Select `quantshift-system-health.json`
   - Select data source: "Prometheus"
   - Click "Import"

3. **Import Trading Performance Dashboard**
   - Repeat steps above with `quantshift-trading-performance.json`

### Verify Data is Flowing

After importing, you should see:

**System Health Dashboard:**
- ✅ Bot Status: < 30 seconds since last heartbeat (green)
- ✅ Symbols Loaded: Equity ~100, Crypto ~50
- ✅ Cycle Duration: Equity ~5-10s, Crypto ~10-20s
- ✅ Cycle Errors: Should be 0 or very low
- ✅ Open Positions: Current position count

**Trading Performance Dashboard:**
- ✅ Portfolio Value: Current account equity
- ✅ Daily P&L: Today's unrealized P&L
- ✅ Portfolio Value Over Time: Line chart showing growth
- ✅ Signals Generated: Rate of signals by strategy
- ✅ Orders Executed: Buy/sell order rate

## Dashboard Files

- `quantshift-system-health.json` - Bot health monitoring
- `quantshift-trading-performance.json` - Trading metrics and P&L

## Prometheus Queries Used

### Health Metrics
```promql
# Time since last heartbeat
time() - quantshift_equity_heartbeat_seconds{component="quantshift_equity"}

# Symbols loaded
quantshift_equity_symbols_loaded{component="quantshift_equity"}

# Average cycle duration (5min rate)
rate(quantshift_equity_cycle_duration_seconds_sum[5m]) / rate(quantshift_equity_cycle_duration_seconds_count[5m])

# Cycle errors rate
rate(quantshift_equity_cycle_errors_total[5m])
```

### Business Metrics
```promql
# Portfolio value
quantshift_equity_portfolio_value_usd{component="quantshift_equity"}

# Daily P&L
quantshift_equity_daily_pnl_usd{component="quantshift_equity"}

# Open positions
quantshift_equity_positions_open{component="quantshift_equity"}

# Signals generated rate
rate(quantshift_signals_generated_total[5m])

# Orders executed rate
rate(quantshift_orders_executed_total[5m])
```

## Customization

### Add Alerts
1. Edit panel
2. Click "Alert" tab
3. Create alert rule:
   - **Bot Down**: `time() - quantshift_equity_heartbeat_seconds > 120`
   - **High Errors**: `rate(quantshift_cycle_errors_total[5m]) > 0.1`
   - **No Positions**: `quantshift_positions_open == 0` (if expected to have positions)

### Adjust Thresholds
- Edit panel → Field → Thresholds
- Modify colors and values as needed

### Add More Panels
Common additions:
- API latency histogram
- Market data age
- Watchdog restart count
- Redis memory usage
- Database connection count

## Troubleshooting

### No Data Showing
1. Check Prometheus targets: http://prometheus.cloudigan.net/targets
   - Look for `quantshift_equity_primary` and `quantshift_crypto_primary`
   - Should show "UP" status
2. Verify metrics endpoint: `curl http://10.92.3.27:9200/metrics`
3. Check bot logs: `ssh quantshift-primary "tail -100 /opt/quantshift/logs/equity-bot.log"`

### Metrics Not Updating
1. Check bot is running: `ssh quantshift-primary "systemctl status quantshift-equity"`
2. Check heartbeat in database: Query `bot_status` table
3. Restart bot if needed: `ssh quantshift-primary "systemctl restart quantshift-equity"`

### Dashboard Shows Old Data
- Check Grafana refresh interval (top right)
- Verify Prometheus scrape interval (should be 15s)
- Check system time on all containers

## Next Steps

After dashboards are working:
1. Create alert rules in Prometheus
2. Configure Alertmanager notifications
3. Build automated failover monitor
4. Add systemd watchdog integration
