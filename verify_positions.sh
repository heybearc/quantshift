#!/bin/bash
# Quick position sync verification script
# Run this via: ssh qs-dashboard 'bash -s' < verify_positions.sh

echo "=== Position Sync Verification ==="
echo ""
echo "Checking database for positions..."
echo ""

export PGPASSWORD='Cloudy_92!'
psql -h 10.92.3.21 -U quantshift -d quantshift << 'EOF'
\echo '--- Total Positions Count ---'
SELECT COUNT(*) as total_positions FROM positions;

\echo ''
\echo '--- Position Details (Top 15) ---'
SELECT 
    bot_name,
    symbol,
    quantity,
    ROUND(entry_price::numeric, 2) as entry,
    ROUND(current_price::numeric, 2) as current,
    ROUND(unrealized_pl::numeric, 2) as pnl,
    TO_CHAR(updated_at, 'HH24:MI:SS') as last_update
FROM positions 
ORDER BY bot_name, symbol 
LIMIT 15;

\echo ''
\echo '--- Bot Status ---'
SELECT 
    bot_name,
    status,
    TO_CHAR(last_heartbeat, 'HH24:MI:SS') as last_heartbeat
FROM bot_status
ORDER BY bot_name;
EOF

echo ""
echo "=== Verification Complete ==="
echo ""
echo "Expected: 14 positions total"
echo "If you see 14 positions, the sync is working!"
echo "If you see 1 or fewer, check bot logs for sync errors."
