#!/bin/bash
# Deploy QuantShift Equity Bot to Paper Trading

set -e

echo "=========================================="
echo "QuantShift Bot Deployment"
echo "=========================================="

# Create log directory
echo "Creating log directory..."
sudo mkdir -p /var/log/quantshift
sudo chmod 755 /var/log/quantshift

# Copy service file
echo "Installing systemd service..."
sudo cp /opt/quantshift/deploy/quantshift-equity-bot.service /etc/systemd/system/

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable service
echo "Enabling service..."
sudo systemctl enable quantshift-equity-bot.service

# Start service
echo "Starting bot..."
sudo systemctl start quantshift-equity-bot.service

# Wait a moment
sleep 2

# Check status
echo ""
echo "=========================================="
echo "Bot Status:"
echo "=========================================="
sudo systemctl status quantshift-equity-bot.service --no-pager

echo ""
echo "=========================================="
echo "Recent Logs:"
echo "=========================================="
sudo tail -20 /var/log/quantshift/equity-bot.log

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Commands:"
echo "  Status:  sudo systemctl status quantshift-equity-bot"
echo "  Stop:    sudo systemctl stop quantshift-equity-bot"
echo "  Restart: sudo systemctl restart quantshift-equity-bot"
echo "  Logs:    sudo tail -f /var/log/quantshift/equity-bot.log"
echo ""
