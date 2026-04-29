#!/bin/bash
# Check service status
set -e

echo "=== Checking service status ==="

systemctl --user status fastapi_app.service || true

echo ""
echo "=== Checking journal for recent errors ==="

journalctl --user -u fastapi_app.service -n 10 --no-pager || true

echo ""
echo "=== Checking for PID file ==="

ls -la /home/trader/no_env/power-option/data/app.pid 2>/dev/null || echo "No PID file found"