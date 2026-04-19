#!/usr/bin/env python3
from __future__ import annotations
import subprocess
import sys
import os

action = sys.argv[1] if len(sys.argv) > 1 else "start"

service = "power-option"
venv = os.path.expanduser("~/no_venv/venv/bin/gunicorn")
main_app = os.path.expanduser("~/no_venv/power-option/main:app")
bind = "127.0.0.1:8000"
pidfile = os.path.expanduser("~/no_venv/power-option/power-option.pid")
cwd = os.path.expanduser("~/no_venv/power-option")

def start():
    subprocess.run([venv, "-w", "1", "-k", "uvicorn.workers.UvicornWorker", main_app, "--bind", bind, "-D", pidfile], cwd=cwd)

def stop():
    subprocess.run(["pkill", "-f", "gunicorn.*power-option"])

def restart():
    stop()
    import time
    time.sleep(1)
    start()

if action == "start":
    start()
elif action == "stop":
    stop()
elif action == "restart":
    restart()