#!/usr/bin/env python3
from __future__ import annotations
import subprocess
import sys
import os
from datetime import datetime

action = sys.argv[1] if len(sys.argv) > 1 else "start"
service = "fastapi_app"
log_file = "/home/trader/no_venv/power-option/data/cron.log"
os.chdir("/home/trader/no_venv/power-option")

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")

CMD = ["sudo", "/usr/bin/systemctl"]

def is_running():
    result = subprocess.run(CMD + ["is-active", service], capture_output=True, text=True)
    return result.returncode == 0

log(f"Cron action: {action}")

if action == "start":
    log(f"Checking {service} status...")
    if is_running():
        log(f"{service} was running at cron time - no action needed")
        print(f"{service} was running - no action needed")
    else:
        result = subprocess.run(CMD + ["start", service], capture_output=True, text=True)
        log(f"Start result: {result.returncode}, stdout: {result.stdout}, stderr: {result.stderr}")
        print(f"{service} started")
elif action == "stop":
    result = subprocess.run(CMD + ["stop", service], capture_output=True, text=True)
    log(f"Stop result: {result.returncode}, stdout: {result.stdout}, stderr: {result.stderr}")
    print(f"{service} stopped")
elif action == "restart":
    result = subprocess.run(CMD + ["restart", service], capture_output=True, text=True)
    log(f"Restart result: {result.returncode}, stdout: {result.stdout}, stderr: {result.stderr}")
    print(f"{service} restarted")