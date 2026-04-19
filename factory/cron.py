#!/usr/bin/env python3
from __future__ import annotations
import subprocess
import sys

action = sys.argv[1] if len(sys.argv) > 1 else "start"
service = "fastapi_app"

def is_running():
    result = subprocess.run(["sudo", "systemctl", "is-active", service], capture_output=True, text=True)
    return result.returncode == 0

if action == "start":
    if is_running():
        print(f"{service} already running")
    else:
        subprocess.run(["sudo", "systemctl", "start", service])
        print(f"{service} started")
elif action == "stop":
    subprocess.run(["sudo", "systemctl", "stop", service])
    print(f"{service} stopped")
elif action == "restart":
    subprocess.run(["sudo", "systemctl", "restart", service])
    print(f"{service} restarted")