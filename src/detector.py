import logging
from datetime import datetime

import httpx

from src.models import TicketEvent

logger = logging.getLogger(__name__)

API_URL = "https://rcbmpapi.ticketgenie.in/ticket/eventlist/o"
TICKET_PAGE_URL = "https://shop.royalchallengers.com/ticket"


async def fetch_from_api() -> list[TicketEvent]:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(API_URL, headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "Accept": "application/json",
            })
            resp.raise_for_status()
            data = resp.json()

        events = []
        for item in data:
            date_str = item.get("EventDate", "")
            try:
                parsed_date = datetime.fromisoformat(date_str).strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                parsed_date = date_str

            is_sold_out = item.get("IsSoldOut", False)
            is_upcoming = item.get("IsUpcoming", False)

            if is_sold_out:
                status = "sold_out"
            elif is_upcoming:
                status = "coming_soon"
            else:
                status = "available"

            events.append(TicketEvent(
                match_title=item.get("EventTitle", "Unknown Match"),
                date=parsed_date,
                venue=item.get("VenueName", "Unknown Venue"),
                ticket_url=item.get("EventURL", TICKET_PAGE_URL),
                status=status,
            ))
        return events

    except (httpx.HTTPError, Exception) as e:
        logger.warning(f"API detection failed: {e}")
        return []
