# Power Option - Build & Troubleshooting

## Troubleshooting Checklist

When the app fails to start or crashes, check these in order:

### 1. Port 8000 Already in Use
```bash
# Check if something is using port 8000
fuser 8000/tcp
# Kill if needed
sudo fuser -k 8000/tcp
```
- Error: `address already in use`

### 2. PID File Permission Issues
```bash
# Check ownership
ls -la /home/trader/no_env/power-option/data/app.pid
# If owned by root, delete it
sudo rm /home/trader/no_env/power-option/data/app.pid
```
- Error: `PermissionError: Permission denied: 'app.pid'`
- Root-owned PID files cause startup crashes

### 3. Log File Issues
```bash
# Check if log file exists and is writable
ls -la /home/trader/no_env/power-option/data/log.txt
# If missing, create
touch /home/trader/no_env/power-option/data/log.txt
```
- Error: `No such file or directory: 'log.txt'`

### 4. systemd Service Errors
```bash
# Check journal for errors
journalctl --user -u fastapi_app.service -n 20 --no-pager
# Check status
systemctl --user status fastapi_app.service
```
- Error codes: `status=1/FAILURE`, `status=3/NOTIMPLEMENTED`

### 5. Broker Authentication Failures
```bash
# Check logs for broker errors
tail -50 /home/trader/no_env/power-option/data/log.txt | grep -i 'auth\|zerodha\|error'
```
- Error: `sys.exit(1)` in broker library
- The app should handle this gracefully (not crash)

### 6. WebSocket Connection Issues
```bash
# Check nginx proxy
curl -s http://127.0.0.1:8000/ws
# Test if app responds
curl -s http://127.0.0.1:8000/
```
- Error: `403 Forbidden` - nginx blocking WebSocket

---

## Code Fixes Verification

Temporary vs Permanent fixes - use checklist above:

| Issue | Fix Type | Permanent? |
|-------|----------|------------|
| Port 8000 in use | Kill process | Yes |
| Root-owned PID | Delete file | Yes (if app runs as trader) |
| Missing log file | Create file | Check file permissions |
| sys.exit(1) crash | Handle SystemExit in api.py | Need your approval for trading_app change |
| nginx WebSocket 403 | Config nginx | Not implemented yet |

---

## Session History (AI Session - Apr 29 2026)

### Issues Found and Resolutions

1. **Root-owned app.pid file**
   - Error: `PermissionError: Permission denied: 'app.pid'`
   - Cause: Previous run created file as root user
   - Fix: `sudo rm /home/trader/no_env/power-option/data/app.pid`
   - Resolution: Permanent - new PID created as trader user

2. **Systemd service incorrect paths**
   - Error: `No such file or directory` for python and working directory
   - Cause: Service file had `/home/trader/power-option/` instead of `/home/trader/no_env/power-option/`
   - Fix: Updated `factory/fastapi_app.service` with correct paths
   - Resolution: Permanent

3. **sys.exit(1) from broker library causing crash loop**
   - Error: Broker authentication failures causing `SystemExit: 1` in zerodha.py
   - Cause: External broker issues (not code related at this time)
   - Fix: Discussed trading_app architecture but user deferred implementation
   - Resolution: Pending - user to decide on architecture changes

4. **Port 8000 in use**
   - Error: `address already in use`
   - Fix: `sudo fuser -k 8000/tcp`
   - Resolution: Temporary - process cleanup

### Always Update BUILD.md with Issues and Resolutions
- Document issues found and how they were resolved
- Mark fixes as Temporary or Permanent
- Note if external steps were required (outside code changes)
- This helps track whether solutions worked permanently