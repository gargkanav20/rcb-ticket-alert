import json
import os
from datetime import datetime, timezone, timedelta

from src.models import TicketEvent

IST = timezone(timedelta(hours=5, minutes=30))
ERROR_THROTTLE_SECONDS = 3600


class StateManager:
    def __init__(self, state_file: str = "state.json"):
        self._state_file = state_file
        self._state = self._load()

    @property
    def notified_events(self) -> dict:
        return self._state.get("notified_events", {})

    def _load(self) -> dict:
        if os.path.exists(self._state_file):
            with open(self._state_file, "r") as f:
                return json.load(f)
        return {
            "notified_events": {},
            "last_error_notification_at": None,
            "last_poll_at": None,
        }

    def save(self):
        with open(self._state_file, "w") as f:
            json.dump(self._state, f, indent=2)

    def should_notify(self, event: TicketEvent) -> bool:
        existing = self._state["notified_events"].get(event.key)
        if existing is None:
            return True
        if existing["last_status"] != event.status and event.status == "available":
            return True
        return False

    def mark_notified(self, event: TicketEvent):
        now = datetime.now(IST).isoformat()
        existing = self._state["notified_events"].get(event.key)
        if existing:
            existing["last_status"] = event.status
            existing["last_notified_at"] = now
            existing["notification_count"] = existing.get("notification_count", 0) + 1
        else:
            self._state["notified_events"][event.key] = {
                "last_status": event.status,
                "first_notified_at": now,
                "last_notified_at": now,
                "notification_count": 1,
            }

    def should_notify_error(self) -> bool:
        last = self._state.get("last_error_notification_at")
        if last is None:
            return True
        last_dt = datetime.fromisoformat(last)
        return (datetime.now(IST) - last_dt).total_seconds() >= ERROR_THROTTLE_SECONDS

    def mark_error_notified(self):
        self._state["last_error_notification_at"] = datetime.now(IST).isoformat()

    def update_last_poll(self):
        self._state["last_poll_at"] = datetime.now(IST).isoformat()
