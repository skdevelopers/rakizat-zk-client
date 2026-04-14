from __future__ import annotations

import tools._bootstrap  # noqa: F401

from config import DB_PATH
from storage.db import get_recent_outbox_records


def main() -> None:
    rows = get_recent_outbox_records(DB_PATH, 100)

    print("=" * 160)
    print(
        f"{'ID':<6}{'RAW_ID':<8}{'USER_ID':<10}{'UID':<8}{'TIMESTAMP':<24}"
        f"{'STATUS':<8}{'PUNCH':<8}{'SENT':<6}{'DEVICE_SN':<20}"
    )
    print("=" * 160)

    for row in rows:
        print(
            f"{row['id']:<6}"
            f"{row['raw_event_id']:<8}"
            f"{row['user_id']:<10}"
            f"{row['uid']:<8}"
            f"{str(row['timestamp']):<24}"
            f"{row['status']:<8}"
            f"{row['punch']:<8}"
            f"{row['sent']:<6}"
            f"{str(row['device_sn']):<20}"
        )

    print("=" * 160)
    print(f"Total outbox rows shown: {len(rows)}")


if __name__ == "__main__":
    main()