import asyncio
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import partial

import httpx

from src.models import TicketEvent

logger = logging.getLogger(__name__)


def format_message(event: TicketEvent) -> str:
    return (
        f"🏏 RCB TICKETS AVAILABLE!\n\n"
        f"Match: {event.match_title}\n"
        f"Date: {event.date}\n"
        f"Venue: {event.venue}\n\n"
        f"🎟️ Book now: {event.ticket_url}"
    )


def format_error_message(error: str) -> str:
    return (
        f"⚠️ RCB Ticket Notifier Error\n\n"
        f"{error}\n\n"
        f"The detection system may need attention."
    )


async def send_telegram(
    event_or_msg: TicketEvent | str,
    bot_token: str,
    chat_id: str,
) -> bool:
    text = format_message(event_or_msg) if isinstance(event_or_msg, TicketEvent) else event_or_msg
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            )
            resp.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"Telegram notification failed: {e}")
        return False


async def send_discord(
    event_or_msg: TicketEvent | str,
    webhook_url: str,
) -> bool:
    if isinstance(event_or_msg, TicketEvent):
        payload = {
            "embeds": [{
                "title": "🏏 RCB TICKETS AVAILABLE!",
                "color": 0xE3263A,
                "fields": [
                    {"name": "Match", "value": event_or_msg.match_title, "inline": False},
                    {"name": "Date", "value": event_or_msg.date, "inline": True},
                    {"name": "Venue", "value": event_or_msg.venue, "inline": True},
                    {"name": "Book Now", "value": f"[Click here]({event_or_msg.ticket_url})", "inline": False},
                ],
            }],
        }
    else:
        payload = {"content": event_or_msg}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(webhook_url, json=payload)
            resp.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"Discord notification failed: {e}")
        return False


def _send_email_sync(
    event_or_msg: TicketEvent | str,
    sender: str,
    app_password: str,
    recipient: str,
) -> bool:
    if isinstance(event_or_msg, TicketEvent):
        subject = f"🏏 RCB Tickets Available: {event_or_msg.match_title}"
        body = format_message(event_or_msg)
    else:
        subject = "⚠️ RCB Ticket Notifier Alert"
        body = event_or_msg

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, app_password)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"Email notification failed: {e}")
        return False


async def send_email(
    event_or_msg: TicketEvent | str,
    sender: str,
    app_password: str,
    recipient: str,
) -> bool:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        partial(_send_email_sync, event_or_msg, sender, app_password, recipient),
    )


async def notify_all(
    event_or_msg: TicketEvent | str,
    telegram_token: str,
    telegram_chat_id: str,
    discord_webhook: str,
    email_sender: str,
    email_password: str,
    email_recipient: str,
) -> dict[str, bool]:
    tg, dc, em = await asyncio.gather(
        send_telegram(event_or_msg, telegram_token, telegram_chat_id),
        send_discord(event_or_msg, discord_webhook),
        send_email(event_or_msg, email_sender, email_password, email_recipient),
    )
    return {"telegram": tg, "discord": dc, "email": em}
