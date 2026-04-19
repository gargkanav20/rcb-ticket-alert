import json
import os
from datetime import datetime, timezone, timedelta
from src.state import StateManager
from src.models import TicketEvent


IST = timezone(timedelta(hours=5, minutes=30))


def _make_event(title="RCB vs CSK", date="2026-05-10", status="available"):
    return TicketEvent(
        match_title=title,
        date=date,
        venue="M. Chinnaswamy Stadium",
        ticket_url="https://shop.royalchallengers.com/ticket",
        status=status,
    )


def test_fresh_state_has_no_notified_events(tmp_path):
    state_file = tmp_path / "state.json"
    mgr = StateManager(str(state_file))
    assert mgr.notified_events == {}


def test_should_notify_new_event(tmp_path):
    state_file = tmp_path / "state.json"
    mgr = StateManager(str(state_file))
    event = _make_event()
    assert mgr.should_notify(event) is True


def test_should_not_notify_already_notified_same_status(tmp_path):
    state_file = tmp_path / "state.json"
    mgr = StateManager(str(state_file))
    event = _make_event()
    mgr.mark_notified(event)
    assert mgr.should_notify(event) is False


def test_should_notify_on_status_change_to_available(tmp_path):
    state_file = tmp_path / "state.json"
    mgr = StateManager(str(state_file))
    sold_out = _make_event(status="sold_out")
    mgr.mark_notified(sold_out)
    available = _make_event(status="available")
    assert mgr.should_notify(available) is True


def test_save_and_load_persists_state(tmp_path):
    state_file = tmp_path / "state.json"
    mgr = StateManager(str(state_file))
    event = _make_event()
    mgr.mark_notified(event)
    mgr.save()

    mgr2 = StateManager(str(state_file))
    assert mgr2.should_notify(event) is False


def test_should_throttle_error_notification(tmp_path):
    state_file = tmp_path / "state.json"
    mgr = StateManager(str(state_file))
    assert mgr.should_notify_error() is True
    mgr.mark_error_notified()
    assert mgr.should_notify_error() is False


def test_error_notification_allowed_after_one_hour(tmp_path):
    state_file = tmp_path / "state.json"
    mgr = StateManager(str(state_file))
    mgr.mark_error_notified()
    one_hour_ago = (datetime.now(IST) - timedelta(hours=1, minutes=1)).isoformat()
    mgr._state["last_error_notification_at"] = one_hour_ago
    assert mgr.should_notify_error() is True


def test_update_last_poll(tmp_path):
    state_file = tmp_path / "state.json"
    mgr = StateManager(str(state_file))
    mgr.update_last_poll()
    assert mgr._state["last_poll_at"] is not None
