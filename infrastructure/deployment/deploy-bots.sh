#!/bin/bash
# Deploy bots to BOTH primary and standby (hot-standby deployment)

set -e

echo "🚀 Deploying QuantShift Bots (Hot-Standby)"
echo "==========================================="

CONTAINERS=("100" "101")
IPS=("10.92.3.27" "10.92.3.28")
NAMES=("primary" "standby")

for i in "${!CONTAINERS[@]}"; do
    CONTAINER="${CONTAINERS[$i]}"
    IP="${IPS[$i]}"
    NAME="${NAMES[$i]}"
    
    echo ""
    echo "📦 Deploying to LXC $CONTAINER ($NAME - $IP)"
    echo "-------------------------------------------"
    
    ssh root@$IP << 'ENDSSH'
        cd /opt/quantshift
        
        # Pull latest code
        echo "⬇️  Pulling latest code..."
        git pull origin main
        
        # Install Python dependencies
        echo "📦 Installing dependencies..."
        pip install -e packages/core
        pip install -e apps/bots/equity
        pip install -e apps/bots/crypto
        
        # Restart services
        echo "🔄 Restarting services..."
        systemctl restart quantshift-equity || echo "⚠️  Equity bot not running yet"
        systemctl restart quantshift-crypto || echo "⚠️  Crypto bot not running yet"
        
        echo "✅ Deployment complete on this container"
ENDSSH
    
    echo "✅ LXC $CONTAINER ($NAME) deployment complete"
done

echo ""
echo "==========================================="
echo "✅ Hot-Standby Deployment Complete!"
echo "==========================================="
echo ""
echo "Both containers now running identical code:"
echo "  - Primary (LXC 100): 10.92.3.27"
echo "  - Standby (LXC 101): 10.92.3.28"
echo ""
echo "HA Proxy will automatically failover if primary fails"
