#!/bin/bash
# QuantShift Admin Platform - Clean Deployment Script
# Prevents stale build issues by ensuring complete rebuild

set -e  # Exit on any error

echo "🚀 Starting QuantShift Admin deployment..."

# Navigate to app directory
cd /opt/quantshift/apps/admin-web || exit 1

# Pull latest code
echo "📥 Pulling latest code from GitHub..."
cd /opt/quantshift
git pull origin main

cd apps/admin-web

# Stop the application
echo "📛 Stopping application..."
pm2 stop quantshift-admin 2>/dev/null || true
pm2 delete quantshift-admin 2>/dev/null || true

# Kill any remaining processes
pkill -9 -f "next-server" 2>/dev/null || true
pkill -9 -f "next start" 2>/dev/null || true
sleep 3

# Clean build artifacts (CRITICAL - prevents stale build issues)
echo "🧹 Cleaning old build artifacts..."
rm -rf .next
rm -rf node_modules/.cache

# Install dependencies (in case package.json changed)
echo "📦 Installing dependencies..."
npm install --production

# Build application
echo "🔨 Building application..."
npm run build

# Verify build succeeded
if [ ! -f ".next/BUILD_ID" ]; then
    echo "❌ Build failed - .next/BUILD_ID not found"
    exit 1
fi

BUILD_ID=$(cat .next/BUILD_ID)
echo "✅ Build successful - Build ID: $BUILD_ID"

# Start with PM2
echo "🚀 Starting application with PM2..."
pm2 start npm --name quantshift-admin -- start

# Wait for startup
sleep 8

# Verify app is responding
echo "🔍 Verifying application..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/login)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Application is running successfully!"
    echo "📊 Build ID: $BUILD_ID"
    pm2 save
    pm2 status
else
    echo "❌ Application failed to start (HTTP $HTTP_CODE)"
    pm2 logs quantshift-admin --lines 20
    exit 1
fi

echo "✨ Deployment complete!"
