from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class LogicState:
    running: bool = False
    started_at: Optional[datetime] = None
    startup_data: Optional[dict] = None
    app_data: Optional[dict] = None
    ws_client: Optional[Any] = None
    background_task: Optional[Any] = None
    paused: bool = False
    pause_until: Optional[datetime] = None
    pause_reason: str = ""

    def is_running(self) -> bool:
        if not self.running:
            return False
        if self.paused:
            return False
        if self.pause_until and datetime.now() > self.pause_until:
            self.paused = False
            self.pause_until = None
        return True

    def is_paused(self) -> bool:
        if not self.paused:
            return False
        if self.pause_until and datetime.now() > self.pause_until:
            self.paused = False
            self.pause_until = None
            return False
        return True

    def reset(self) -> None:
        self.running = False
        self.started_at = None
        self.startup_data = None
        self.app_data = None
        self.ws_client = None
        self.background_task = None
        self.paused = False
        self.pause_until = None
        self.pause_reason = ""


_logic_state = LogicState()


def get_logic_state() -> LogicState:
    return _logic_state
