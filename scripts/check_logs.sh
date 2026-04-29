#!/bin/bash
# Check application and system logs for errors
set -e

echo "=== Application Logs (last 30 lines) ==="
tail -30 ../data/log.txt

echo ""
echo "=== Journal Logs (last 10 lines) ==="
journalctl --user -u fastapi_app.service -n 10 --no-pager 2>/dev/null || true

echo ""
echo "=== WebSocket Errors ==="
grep -i "error\|close\|fail" ../data/log.txt | tail -10 && echo "Errors found!" || echo "No errors"

echo ""
echo "=== Log check complete ==="