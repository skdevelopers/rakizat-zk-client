"""
Test pushing unsent records to Laravel.
"""

from __future__ import annotations

import json

from config import BATCH_SIZE, DB_PATH
from core.attendance import collect_attendance
from services.api_client import send_attendance_batch
from storage.db import mark_records_sent


def main() -> None:
    """
    Push unsent attendance rows once.
    """
    records, _ = collect_attendance(BATCH_SIZE)

    if not records:
        print("No valid unsent records found.")
        return

    response = send_attendance_batch(records)
    print("API response:")
    print(json.dumps(response, indent=2, ensure_ascii=False))

    ids = [int(item["local_id"]) for item in response.get("accepted", []) if "local_id" in item]

    if ids:
        mark_records_sent(DB_PATH, ids, api_response=json.dumps(response, ensure_ascii=False))
        print(f"Marked {len(ids)} records as sent.")
    else:
        print("No accepted records returned by API.")


if __name__ == "__main__":
    main()