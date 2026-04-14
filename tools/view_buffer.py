"""
View local attendance buffer rows.
"""

from __future__ import annotations

import tools._bootstrap  # noqa: F401

from config import DB_PATH
from storage.db import get_all_records


def main() -> None:
    """
    Print attendance buffer rows.
    """
    rows = get_all_records(DB_PATH, limit=500)

    if not rows:
        print("No records found.")
        return

    print("=" * 150)
    print(
        f"{'ID':<6} {'USER_ID':<15} {'DEVICE_SN':<20} {'TIMESTAMP':<22} "
        f"{'STATUS':<8} {'PUNCH':<8} {'SENT':<6} {'DEVICE_IP':<16}"
    )
    print("=" * 150)

    for row in rows:
        print(
            f"{row['id']:<6}"
            f"{str(row['user_id']):<15}"
            f"{str(row['device_sn']):<20}"
            f"{str(row['timestamp']):<22}"
            f"{str(row['status']):<8}"
            f"{str(row['punch']):<8}"
            f"{str(row['sent']):<6}"
            f"{str(row['device_ip']):<16}"
        )

    print("=" * 150)
    print(f"Total rows shown: {len(rows)}")


if __name__ == "__main__":
    main()