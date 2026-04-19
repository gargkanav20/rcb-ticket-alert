import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

from src.detector import detect_tickets
from src.notifier import notify_all, format_error_message
from src.state import StateManager

load_dotenv()

IST = timezone(timedelta(hours=5, minutes=30))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("rcb-notifier")


def get_config() -> dict:
    required = {
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
        "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID"),
        "DISCORD_WEBHOOK_URL": os.getenv("DISCORD_WEBHOOK_URL"),
        "EMAIL_SENDER": os.getenv("EMAIL_SENDER"),
        "EMAIL_APP_PASSWORD": os.getenv("EMAIL_APP_PASSWORD"),
        "EMAIL_RECIPIENT": os.getenv("EMAIL_RECIPIENT"),
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        logger.error(f"Missing required env vars: {', '.join(missing)}")
        sys.exit(1)
    return required


async def poll_once(state: StateManager, config: dict, dry_run: bool = False):
    logger.info(f"Polling at {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')}")
    state.update_last_poll()

    events, errors = await detect_tickets()

    if errors and state.should_notify_error():
        error_msg = format_error_message("\n".join(errors))
        logger.warning(f"Detection errors: {errors}")
        if not dry_run:
            await notify_all(
                error_msg,
                config["TELEGRAM_BOT_TOKEN"],
                config["TELEGRAM_CHAT_ID"],
                config["DISCORD_WEBHOOK_URL"],
                config["EMAIL_SENDER"],
                config["EMAIL_APP_PASSWORD"],
                config["EMAIL_RECIPIENT"],
            )
            state.mark_error_notified()
        else:
            logger.info(f"[DRY RUN] Would send error notification: {error_msg}")

    if not events:
        logger.info("No events found")
        state.save()
        return

    logger.info(f"Found {len(events)} events")
    for event in events:
        logger.info(f"  {event.key} -> {event.status}")
        if state.should_notify(event):
            logger.info(f"  -> NEW/CHANGED, notifying!")
            if not dry_run:
                results = await notify_all(
                    event,
                    config["TELEGRAM_BOT_TOKEN"],
                    config["TELEGRAM_CHAT_ID"],
                    config["DISCORD_WEBHOOK_URL"],
                    config["EMAIL_SENDER"],
                    config["EMAIL_APP_PASSWORD"],
                    config["EMAIL_RECIPIENT"],
                )
                logger.info(f"  -> Results: {results}")
                all_failed = not any(results.values())
                if all_failed:
                    logger.error("All notification channels failed, retrying in 30s")
                    await asyncio.sleep(30)
                    results = await notify_all(
                        event,
                        config["TELEGRAM_BOT_TOKEN"],
                        config["TELEGRAM_CHAT_ID"],
                        config["DISCORD_WEBHOOK_URL"],
                        config["EMAIL_SENDER"],
                        config["EMAIL_APP_PASSWORD"],
                        config["EMAIL_RECIPIENT"],
                    )
                    logger.info(f"  -> Retry results: {results}")
            else:
                logger.info(f"[DRY RUN] Would notify: {event.match_title} ({event.status})")
            state.mark_notified(event)
        else:
            logger.info(f"  -> Already notified, skipping")

    state.save()


async def run(duration_minutes: int, interval_seconds: int, dry_run: bool = False):
    config = get_config()
    state_path = os.getenv("STATE_FILE_PATH", "state.json")
    state = StateManager(state_path)

    if duration_minutes == 0:
        logger.info("Running indefinitely (Ctrl+C to stop)")
        while True:
            await poll_once(state, config, dry_run)
            logger.info(f"Sleeping {interval_seconds}s until next poll...")
            await asyncio.sleep(interval_seconds)
    else:
        end_time = datetime.now(IST).timestamp() + (duration_minutes * 60)
        logger.info(f"Running for {duration_minutes} minutes, polling every {interval_seconds}s")
        while datetime.now(IST).timestamp() < end_time:
            await poll_once(state, config, dry_run)
            remaining = end_time - datetime.now(IST).timestamp()
            if remaining <= interval_seconds:
                logger.info("Time limit approaching, exiting cleanly")
                break
            logger.info(f"Sleeping {interval_seconds}s until next poll...")
            await asyncio.sleep(interval_seconds)

    logger.info("Done")


def main():
    parser = argparse.ArgumentParser(description="RCB Ticket Availability Notifier")
    parser.add_argument(
        "--duration", type=int, default=0,
        help="Minutes to run (0 = indefinitely). Default: 0",
    )
    parser.add_argument(
        "--interval", type=int, default=120,
        help="Seconds between polls. Default: 120",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print notifications instead of sending them",
    )
    args = parser.parse_args()
    asyncio.run(run(args.duration, args.interval, args.dry_run))


if __name__ == "__main__":
    main()
