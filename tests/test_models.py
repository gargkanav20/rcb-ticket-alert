from src.models import TicketEvent


def test_ticket_event_creation():
    event = TicketEvent(
        match_title="RCB vs CSK",
        date="2026-05-10",
        venue="M. Chinnaswamy Stadium",
        ticket_url="https://shop.royalchallengers.com/ticket",
        status="available",
    )
    assert event.match_title == "RCB vs CSK"
    assert event.date == "2026-05-10"
    assert event.venue == "M. Chinnaswamy Stadium"
    assert event.status == "available"


def test_ticket_event_composite_key():
    event = TicketEvent(
        match_title="RCB vs CSK",
        date="2026-05-10",
        venue="M. Chinnaswamy Stadium",
        ticket_url="https://shop.royalchallengers.com/ticket",
        status="available",
    )
    assert event.key == "RCB vs CSK|2026-05-10"


def test_ticket_event_equality_by_key():
    event1 = TicketEvent(
        match_title="RCB vs CSK",
        date="2026-05-10",
        venue="M. Chinnaswamy Stadium",
        ticket_url="https://shop.royalchallengers.com/ticket",
        status="available",
    )
    event2 = TicketEvent(
        match_title="RCB vs CSK",
        date="2026-05-10",
        venue="M. Chinnaswamy Stadium",
        ticket_url="https://shop.royalchallengers.com/ticket",
        status="sold_out",
    )
    assert event1.key == event2.key


def test_ticket_event_to_dict():
    event = TicketEvent(
        match_title="RCB vs CSK",
        date="2026-05-10",
        venue="M. Chinnaswamy Stadium",
        ticket_url="https://shop.royalchallengers.com/ticket",
        status="available",
    )
    d = event.to_dict()
    assert d == {
        "match_title": "RCB vs CSK",
        "date": "2026-05-10",
        "venue": "M. Chinnaswamy Stadium",
        "ticket_url": "https://shop.royalchallengers.com/ticket",
        "status": "available",
    }
