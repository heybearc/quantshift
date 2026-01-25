#!/bin/bash
# Deploy dashboard to single instance (LXC 137)

set -e

echo "🚀 Deploying QuantShift Dashboard"
echo "=================================="

DASHBOARD_IP="10.92.3.29"

echo ""
echo "📦 Deploying to LXC 137 (Dashboard - $DASHBOARD_IP)"
echo "---------------------------------------------------"

ssh root@$DASHBOARD_IP << 'ENDSSH'
    cd /opt/quantshift
    
    # Pull latest code
    echo "⬇️  Pulling latest code..."
    git pull origin main
    
    # Install dependencies
    echo "📦 Installing dependencies..."
    npm install
    
    # Generate Prisma client
    echo "🔧 Generating Prisma client..."
    npx prisma generate
    
    # Build Next.js
    echo "🏗️  Building Next.js..."
    npm run build
    
    # Reload with PM2 (zero-downtime)
    echo "🔄 Reloading with PM2..."
    pm2 reload quantshift-admin || pm2 start ecosystem.config.js
    
    echo "✅ Dashboard deployment complete"
ENDSSH

echo ""
echo "=================================="
echo "✅ Dashboard Deployment Complete!"
echo "=================================="
echo ""
echo "Dashboard running at:"
echo "  - LXC 137: 10.92.3.29:3000"
echo "  - Public: https://trader.cloudigan.net"
