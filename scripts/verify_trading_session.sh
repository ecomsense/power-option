#!/bin/bash
# Verify trading session is running correctly and new token generated
set -e

echo "=== Verifying trading session ==="

# Check logic status
STATUS=$(curl -sf http://127.0.0.1:8000/api/logic/status || echo "{}")
IS_RUNNING=$(echo "$STATUS" | jq -r '.running' 2>/dev/null || echo "error")
SESSION_ID=$(echo "$STATUS" | jq -r '.session_id' 2>/dev/null || echo "null")

echo "Running: $IS_RUNNING"
echo "Session ID: $SESSION_ID"

# Check logs for new token
echo ""
echo "=== Checking for new token in logs ==="
tail -20 ../data/log.txt | grep -i "token" && echo "Token found!" || echo "No token in recent logs"

# Check if reset-all was called
echo ""
echo "=== Checking reset-all ==="
grep -i "token file deleted" ../data/log.txt && echo "Reset was called!" || echo "Reset not called"

if [ "$IS_RUNNING" = "true" ]; then
    echo ""
    echo "=== Trading session is running ==="
else
    echo ""
    echo "=== Trading session NOT running ==="
fi

echo "=== Verification complete ==="