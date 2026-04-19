# RCB Ticket Availability Notifier

Monitors [RCB IPL match ticket availability](https://shop.royalchallengers.com/ticket) and sends instant notifications via **Telegram**, **Discord**, and **Email** when tickets become available.

## How It Works

1. **Detection** — Polls two sources in parallel every 2 minutes:
   - RCB's ticket API (`rcbmpapi.ticketgenie.in`)
   - The ticket page via headless browser (Playwright)
2. **Deduplication** — Merges results, tracks what you've already been notified about
3. **Notification** — Fires Telegram, Discord, and Email simultaneously
4. **Re-release detection** — If a sold-out match becomes available again, you get notified

## Quick Start (Local)

```bash
# Clone and install
git clone git@github-personal:gargkanav20/rcb-ticket-alert.git
cd rcb-ticket-alert
pip install -r requirements.txt
playwright install chromium

# Configure
cp .env.example .env
# Edit .env with your Telegram, Discord, and Email credentials

# Run (polls every 2 minutes until you stop it)
python -m src.main

# Dry run (prints instead of sending notifications)
python -m src.main --dry-run

# Custom interval and duration
python -m src.main --interval 60 --duration 30
```

## Setup: Notification Channels

### Telegram
1. Message [@BotFather](https://t.me/botfather) on Telegram, create a bot, copy the token
2. Message your bot, then visit `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your `chat_id`

### Discord
1. Go to your Discord server → Settings → Integrations → Webhooks
2. Create a webhook, copy the URL

### Email (Gmail)
1. Enable 2FA on your Google account
2. Go to [App Passwords](https://myaccount.google.com/apppasswords), generate one for "Mail"
3. Use that app password (not your real password)

## GitHub Actions (Always-On)

The included workflow runs every hour, polling every 2 minutes internally.

1. Fork/push this repo (must be **public** for unlimited Actions minutes)
2. Go to repo Settings → Secrets and variables → Actions
3. Add these secrets:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `DISCORD_WEBHOOK_URL`
   - `EMAIL_SENDER`
   - `EMAIL_APP_PASSWORD`
   - `EMAIL_RECIPIENT`
4. The workflow starts automatically on the next hour, or trigger manually from Actions tab

## Testing

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```
