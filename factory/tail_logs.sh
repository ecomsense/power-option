#!/bin/bash
# Create tmux with 3 panes: app, nginx, gunicorn
tmux new-session -d -s logs 'tail -f ~/power-option/data/log.txt'
tmux split-window -h 'sudo tail -f /var/log/nginx/access.log'
tmux select-pane -t 0
tmux split-window -v 'journalctl -u fastapi_app -f --no-pager'
tmux select-layout -t logs tiled
tmux attach-session -t logs