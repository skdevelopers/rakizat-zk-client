"""
Prepare local unsent outbox rows for Laravel API push.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from loguru import logger

from config import BATCH_SIZE, DB_PATH
from storage.db import get_unsent_records


def collect_attendance(limit: int = BATCH_SIZE) -> Tuple[List[Dict], List[Dict]]:
    rows = get_unsent_records(DB_PATH, limit)
    logger.info("Collecting {} unsent outbox rows", len(rows))

    records: List[Dict] = []

    for row in rows:
        records.append({
            "local_id": int(row["id"]),
            "device_name": row["device_name"],
            "device_ip": row["device_ip"],
            "device_sn": row["device_sn"],
            "uid": int(row["uid"]),
            "user_id": int(row["user_id"]),
            "timestamp": str(row["timestamp"]),
            "status": int(row["status"]),
            "punch": int(row["punch"]),
        })

    return records, rows