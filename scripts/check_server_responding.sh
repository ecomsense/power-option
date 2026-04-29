#!/bin/bash
# Check if server is responding
set -e

echo "=== Checking server responding ==="

curl -sf http://127.0.0.1:8000/ >/dev/null && echo "Root endpoint OK" || echo "Root endpoint FAILED"

curl -sf http://127.0.0.1:8000/api/schedule >/dev/null && echo "Schedule API OK" || echo "Schedule API FAILED"

curl -sf http://127.0.0.1:8000/api/logic/status >/dev/null && echo "Logic status API OK" || echo "Logic status API FAILED"

echo "=== Checking for WebSocket errors ==="
grep -i "1006\|close.*unclean\|error" ../data/log.txt | tail -5 && echo "WebSocket issues found" || echo "No WebSocket errors"

echo "=== Server check complete ==="