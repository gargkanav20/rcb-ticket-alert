import logging
import re
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


def _parse_playwright_html(html: str) -> list[TicketEvent]:
    events = []
    date_pattern = re.compile(
        r"(\w+day),?\s+(\w+)\s+(\d{1,2}),?\s+(\d{4})\s+(\d{1,2}:\d{2}\s*[AP]M)",
        re.IGNORECASE,
    )

    event_cards = re.split(r'class="event-card"', html)[1:]

    for card in event_cards:
        date_match = date_pattern.search(card)
        if not date_match:
            continue

        month_str = date_match.group(2)
        day_str = date_match.group(3)
        year_str = date_match.group(4)

        try:
            parsed = datetime.strptime(f"{month_str} {day_str} {year_str}", "%B %d %Y")
            date_formatted = parsed.strftime("%Y-%m-%d")
        except ValueError:
            try:
                parsed = datetime.strptime(f"{month_str} {day_str} {year_str}", "%b %d %Y")
                date_formatted = parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue

        title_match = re.search(r"<h3[^>]*>([^<]+)</h3>", card)
        title = title_match.group(1).strip() if title_match else "Unknown Match"

        venue_match = re.search(r'class="venue"[^>]*>([^<]+)<', card)
        venue = venue_match.group(1).strip() if venue_match else "M. Chinnaswamy Stadium"

        url_match = re.search(r'href="(/ticket/[^"]+)"', card)
        ticket_url = f"https://shop.royalchallengers.com{url_match.group(1)}" if url_match else TICKET_PAGE_URL

        is_sold_out = "sold-out" in card.lower() or "sold out" in card.lower()
        status = "sold_out" if is_sold_out else "available"

        events.append(TicketEvent(
            match_title=title,
            date=date_formatted,
            venue=venue,
            ticket_url=ticket_url,
            status=status,
        ))

    return events


async def fetch_from_playwright() -> list[TicketEvent]:
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(TICKET_PAGE_URL, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            html = await page.content()
            await browser.close()

        return _parse_playwright_html(html)

    except Exception as e:
        logger.warning(f"Playwright detection failed: {e}")
        return []
