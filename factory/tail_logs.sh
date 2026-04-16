#!/bin/bash
# Simple all-logs watcher (needs sudo for nginx)

# App logs
tail -f ~/power-option/data/log.txt &

# Gunicorn service logs
journalctl -u fastapi_app -f --no-pager &

# Nginx logs (needs sudo)
sudo tail -f /var/log/nginx/access.log &

wait