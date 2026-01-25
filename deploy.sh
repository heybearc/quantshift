#!/bin/bash
set -e

echo "=== QuantShift Deployment Script ==="
echo "Starting deployment at $(date)"

cd /opt/quantshift

echo "1. Stopping all processes..."
pm2 delete all 2>/dev/null || true
pkill -9 node 2>/dev/null || true
sleep 2

if lsof -i :3001 > /dev/null 2>&1; then
    echo "ERROR: Port 3001 still in use!"
    lsof -i :3001
    exit 1
fi

echo "2. Cleaning old build..."
rm -rf .next

echo "3. Building application..."
npm run build

if [ ! -f ".next/BUILD_ID" ]; then
    echo "ERROR: Build failed - no BUILD_ID found"
    exit 1
fi

BUILD_ID=$(cat .next/BUILD_ID)
VERSION=$(grep -o "\"version\": \"[^\"]*\"" package.json | cut -d'" -f4)
echo "   Build ID: $BUILD_ID"
echo "   Version: $VERSION"

echo "4. Starting application..."
pm2 start npm --name quantshift-admin -- start

sleep 5

if ! lsof -i :3001 > /dev/null 2>&1; then
    echo "ERROR: Application failed to start on port 3001"
    pm2 logs quantshift-admin --lines 50
    exit 1
fi

echo "5. Testing application..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/login)
if [ "$HTTP_CODE" != "200" ]; then
    echo "ERROR: Application not responding correctly (HTTP $HTTP_CODE)"
    exit 1
fi

pm2 save

echo ""
echo "=== Deployment Successful ==="
echo "Version: $VERSION"
echo "Build ID: $BUILD_ID"
echo "Port: 3001"
echo "Status: Running"
echo "Completed at $(date)"
