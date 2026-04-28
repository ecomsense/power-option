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


_logic_state = LogicState()


def get_logic_state() -> LogicState:
    return _logic_state
