#!/bin/bash
# Watch app logs and nginx in separate windows (3 splits)
multitail -s 3 \
    ~/power-option/data/log.txt \
    ~/power-option/data/log.txt \
    /var/log/nginx/access.log