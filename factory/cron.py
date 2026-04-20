#!/usr/bin/env python3
from __future__ import annotations
import subprocess
import sys
import os
from datetime import datetime

action = sys.argv[1] if len(sys.argv) > 1 else "start"
service = "fastapi_app"
log_file = "/home/trader/no_venv/power-option/data/cron.log"

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")

def is_running():
    result = subprocess.run(["sudo", "systemctl", "is-active", service], capture_output=True, text=True)
    return result.returncode == 0

log(f"Cron action: {action}")

if action == "start":
    if is_running():
        log(f"{service} already running")
        print(f"{service} already running")
    else:
        result = subprocess.run(["sudo", "systemctl", "start", service], capture_output=True, text=True)
        log(f"Start result: {result.returncode}")
        print(f"{service} started")
elif action == "stop":
    result = subprocess.run(["sudo", "systemctl", "stop", service], capture_output=True, text=True)
    log(f"Stop result: {result.returncode}")
    print(f"{service} stopped")
elif action == "restart":
    result = subprocess.run(["sudo", "systemctl", "restart", service], capture_output=True, text=True)
    log(f"Restart result: {result.returncode}")
    print(f"{service} restarted")