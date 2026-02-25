#!/bin/bash
# Install QuantShift Failover Monitor on STANDBY container (CT 101)
# Run this script on the standby container

set -e

echo "=== Installing QuantShift Failover Monitor ==="

# Check we're on standby
HOSTNAME=$(hostname)
if [[ "$HOSTNAME" != *"standby"* ]]; then
    echo "WARNING: This script should run on STANDBY container"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Copy failover monitor script
echo "Copying failover monitor script..."
cp /opt/quantshift/infrastructure/scripts/failover_monitor.py /opt/quantshift/scripts/
chmod +x /opt/quantshift/scripts/failover_monitor.py

# Copy systemd service
echo "Installing systemd service..."
cp /opt/quantshift/infrastructure/scripts/quantshift-failover-monitor.service /etc/systemd/system/

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload

# Enable service (but don't start yet)
echo "Enabling failover monitor service..."
systemctl enable quantshift-failover-monitor.service

echo ""
echo "=== Installation Complete ==="
echo ""
echo "To start the failover monitor:"
echo "  systemctl start quantshift-failover-monitor"
echo ""
echo "To check status:"
echo "  systemctl status quantshift-failover-monitor"
echo ""
echo "To view logs:"
echo "  journalctl -u quantshift-failover-monitor -f"
echo ""
echo "IMPORTANT: Only run this on STANDBY container!"
echo "The monitor will trigger failover if primary goes down."
