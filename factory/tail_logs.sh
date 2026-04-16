#!/bin/bash
# Usage: ./tail_logs.sh [app|nginx|all|svc]
# Default: app only

case "${1:-app}" in
    app)
        multitail ~/power-option/data/log.txt
        ;;
    nginx)
        multitail /var/log/nginx/access.log /var/log/nginx/error.log
        ;;
    all)
        multitail ~/power-option/data/log.txt -I /var/log/nginx/access.log
        ;;
    svc)
        # Gunicorn service logs (no sudo needed)
        journalctl -u fastapi_app -f --no-pager
        ;;
esac