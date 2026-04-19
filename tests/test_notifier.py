import pytest
import httpx
import respx
from unittest.mock import patch, MagicMock
from src.notifier import send_telegram, send_discord, send_email, notify_all, format_message
from src.models import TicketEvent


def _make_event():
    return TicketEvent(
        match_title="RCB vs CSK",
        date="2026-05-10",
        venue="M. Chinnaswamy Stadium",
        ticket_url="https://shop.royalchallengers.com/ticket",
        status="available",
    )


def test_format_message():
    event = _make_event()
    msg = format_message(event)
    assert "RCB vs CSK" in msg
    assert "2026-05-10" in msg
    assert "Chinnaswamy" in msg
    assert "shop.royalchallengers.com" in msg


@pytest.mark.asyncio
async def test_send_telegram_success():
    event = _make_event()
    with respx.mock:
        respx.post("https://api.telegram.org/botTEST_TOKEN/sendMessage").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        result = await send_telegram(
            event, bot_token="TEST_TOKEN", chat_id="12345"
        )
    assert result is True


@pytest.mark.asyncio
async def test_send_telegram_failure():
    event = _make_event()
    with respx.mock:
        respx.post("https://api.telegram.org/botTEST_TOKEN/sendMessage").mock(
            return_value=httpx.Response(500)
        )
        result = await send_telegram(
            event, bot_token="TEST_TOKEN", chat_id="12345"
        )
    assert result is False


@pytest.mark.asyncio
async def test_send_discord_success():
    event = _make_event()
    with respx.mock:
        respx.post("https://discord.com/api/webhooks/test/hook").mock(
            return_value=httpx.Response(204)
        )
        result = await send_discord(
            event, webhook_url="https://discord.com/api/webhooks/test/hook"
        )
    assert result is True


@pytest.mark.asyncio
async def test_send_discord_failure():
    event = _make_event()
    with respx.mock:
        respx.post("https://discord.com/api/webhooks/test/hook").mock(
            return_value=httpx.Response(500)
        )
        result = await send_discord(
            event, webhook_url="https://discord.com/api/webhooks/test/hook"
        )
    assert result is False


@pytest.mark.asyncio
async def test_send_email_success():
    event = _make_event()
    with patch("src.notifier.smtplib") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.SMTP_SSL.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.SMTP_SSL.return_value.__exit__ = MagicMock(return_value=False)
        result = await send_email(
            event,
            sender="test@gmail.com",
            app_password="pass",
            recipient="me@gmail.com",
        )
    assert result is True


@pytest.mark.asyncio
async def test_notify_all_partial_failure():
    event = _make_event()
    with respx.mock:
        respx.post("https://api.telegram.org/botTOK/sendMessage").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        respx.post("https://discord.com/api/webhooks/t/h").mock(
            return_value=httpx.Response(500)
        )
        with patch("src.notifier.smtplib") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.SMTP_SSL.return_value.__enter__ = MagicMock(return_value=mock_server)
            mock_smtp.SMTP_SSL.return_value.__exit__ = MagicMock(return_value=False)

            results = await notify_all(
                event,
                telegram_token="TOK",
                telegram_chat_id="123",
                discord_webhook="https://discord.com/api/webhooks/t/h",
                email_sender="a@b.com",
                email_password="p",
                email_recipient="c@d.com",
            )

    assert results["telegram"] is True
    assert results["discord"] is False
    assert results["email"] is True
