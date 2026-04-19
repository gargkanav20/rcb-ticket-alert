import pytest
import httpx
import respx
from src.detector import fetch_from_api
from src.models import TicketEvent


MOCK_API_RESPONSE = [
    {
        "EventTitle": "Royal Challengers Bengaluru vs Chennai Super Kings",
        "EventDate": "2026-05-10T19:30:00",
        "VenueName": "M. Chinnaswamy Stadium, Bengaluru",
        "EventURL": "https://shop.royalchallengers.com/ticket/rcb-vs-csk",
        "IsSoldOut": False,
        "IsUpcoming": False,
    },
    {
        "EventTitle": "Royal Challengers Bengaluru vs Mumbai Indians",
        "EventDate": "2026-05-15T15:30:00",
        "VenueName": "M. Chinnaswamy Stadium, Bengaluru",
        "EventURL": "https://shop.royalchallengers.com/ticket/rcb-vs-mi",
        "IsSoldOut": True,
        "IsUpcoming": False,
    },
]

MOCK_API_RESPONSE_EMPTY = []


@pytest.mark.asyncio
async def test_fetch_from_api_parses_events():
    with respx.mock:
        respx.get("https://rcbmpapi.ticketgenie.in/ticket/eventlist/o").mock(
            return_value=httpx.Response(200, json=MOCK_API_RESPONSE)
        )
        events = await fetch_from_api()

    assert len(events) == 2
    assert events[0].match_title == "Royal Challengers Bengaluru vs Chennai Super Kings"
    assert events[0].date == "2026-05-10"
    assert events[0].status == "available"
    assert events[1].status == "sold_out"


@pytest.mark.asyncio
async def test_fetch_from_api_handles_empty_response():
    with respx.mock:
        respx.get("https://rcbmpapi.ticketgenie.in/ticket/eventlist/o").mock(
            return_value=httpx.Response(200, json=MOCK_API_RESPONSE_EMPTY)
        )
        events = await fetch_from_api()

    assert events == []


@pytest.mark.asyncio
async def test_fetch_from_api_returns_empty_on_error():
    with respx.mock:
        respx.get("https://rcbmpapi.ticketgenie.in/ticket/eventlist/o").mock(
            return_value=httpx.Response(500)
        )
        events = await fetch_from_api()

    assert events == []


@pytest.mark.asyncio
async def test_fetch_from_api_returns_empty_on_network_error():
    with respx.mock:
        respx.get("https://rcbmpapi.ticketgenie.in/ticket/eventlist/o").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        events = await fetch_from_api()

    assert events == []
