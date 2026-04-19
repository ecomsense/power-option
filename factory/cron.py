#!/usr/bin/env python3
from __future__ import annotations
import subprocess
import sys

action = sys.argv[1] if len(sys.argv) > 1 else "start"
service = "fastapi_app"

if action == "start":
    subprocess.run(["sudo", "systemctl", "start", service])
elif action == "stop":
    subprocess.run(["sudo", "systemctl", "stop", service])
elif action == "restart":
    subprocess.run(["sudo", "systemctl", "restart", service])