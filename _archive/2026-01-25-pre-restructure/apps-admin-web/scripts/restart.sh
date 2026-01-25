#!/bin/bash
# QuantShift Admin Platform - Clean Restart Script

echo "🔄 Starting QuantShift Admin restart..."

# Stop PM2 process
echo "📛 Stopping PM2 process..."
pm2 stop quantshift-admin 2>/dev/null || true
pm2 delete quantshift-admin 2>/dev/null || true

# Kill any remaining Next.js processes
echo "🔪 Killing any remaining Next.js processes..."
pkill -9 -f "next-server" 2>/dev/null || true
pkill -9 -f "next start" 2>/dev/null || true

# Wait for port to be released
echo "⏳ Waiting for port 3001 to be released..."
sleep 3

# Verify port is free
if lsof -ti:3001 > /dev/null 2>&1; then
    echo "⚠️  Port 3001 still in use, force killing..."
    lsof -ti:3001 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Navigate to app directory
cd /opt/quantshift/apps/admin-web || exit 1

# Start with PM2
echo "🚀 Starting QuantShift Admin with PM2..."
pm2 start npm --name quantshift-admin -- start

# Wait for startup
sleep 5

# Check status
echo "📊 PM2 Status:"
pm2 status

# Save PM2 configuration
echo "💾 Saving PM2 configuration..."
pm2 save

# Verify app is responding
echo "🔍 Verifying app is responding..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/login | grep -q "200"; then
    echo "✅ QuantShift Admin is running successfully!"
else
    echo "❌ QuantShift Admin failed to start properly"
    pm2 logs quantshift-admin --lines 20
    exit 1
fi

echo "✨ Restart complete!"
