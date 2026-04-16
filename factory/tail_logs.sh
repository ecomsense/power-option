#!/bin/bash
# Usage: ./tail_logs.sh [app|nginx|all]
# Default: app only

case "${1:-app}" in
    app)
        multitail ~/power-option/data/log.txt
        ;;
    nginx)
        sudo multitail /var/log/nginx/access.log /var/log/nginx/error.log
        ;;
    all)
        multitail ~/power-option/data/log.txt -I /var/log/nginx/access.log
        ;;
esac