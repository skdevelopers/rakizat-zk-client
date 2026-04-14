from __future__ import annotations

import json
import time
from pathlib import Path

from loguru import logger

from config import BATCH_SIZE, DB_PATH, DEVICES, PULL_INTERVAL_SECONDS, SYNC_INTERVAL_MINUTES
from core.attendance import collect_attendance
from core.device_sync import process_device
from services.api_client import send_attendance_batch
from storage.db import mark_records_sent


BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger.remove()
logger.add(LOG_DIR / "zkclient.log", rotation="10 MB", retention=10, level="INFO")
logger.add(lambda msg: print(msg, end=""), level="INFO")


def pull_all_devices() -> None:
    if not DEVICES:
        logger.warning("No devices configured")
        return

    for device in DEVICES:
        process_device(device, DB_PATH)


def push_unsent_records() -> None:
    records, _ = collect_attendance(BATCH_SIZE)

    if not records:
        logger.info("No valid outbox rows to send")
        return

    response = send_attendance_batch(records)

    accepted_items = response.get("accepted", [])
    accepted_ids = [
        int(item["local_id"])
        for item in accepted_items
        if isinstance(item, dict) and "local_id" in item
    ]

    if accepted_ids:
        mark_records_sent(
            DB_PATH,
            accepted_ids,
            api_response=json.dumps(response, ensure_ascii=False),
        )
        logger.success("Marked {} outbox rows as sent", len(accepted_ids))
    else:
        logger.warning("API returned no accepted local_id rows")


def main() -> None:
    logger.info("ZK client started")
    logger.info("Configured devices: {}", len(DEVICES))
    logger.info("Pull interval: {} sec", PULL_INTERVAL_SECONDS)
    logger.info("Push interval: {} min", SYNC_INTERVAL_MINUTES)

    last_push_at = 0.0
    push_every_seconds = max(15, SYNC_INTERVAL_MINUTES * 60)

    while True:
        try:
            pull_all_devices()

            now = time.time()
            if now - last_push_at >= push_every_seconds:
                push_unsent_records()
                last_push_at = now

        except KeyboardInterrupt:
            logger.warning("ZK client stopped by keyboard")
            break
        except Exception as exc:
            logger.exception("Main loop failure: {}", exc)

        time.sleep(max(5, PULL_INTERVAL_SECONDS))


if __name__ == "__main__":
    main()