from __future__ import annotations

import tools._bootstrap  # noqa: F401

from config import DB_PATH
from storage.db import get_recent_raw_events


def main() -> None:
    rows = get_recent_raw_events(DB_PATH, 100)

    print("=" * 180)
    print(
        f"{'ID':<6}{'RAW_UID':<10}{'RAW_USER_ID':<15}{'RAW_TIME':<24}"
        f"{'NUM_UID':<10}{'NUM_USER_ID':<12}{'OK_TIME':<8}{'READY':<8}{'NOTES':<40}"
    )
    print("=" * 180)

    for row in rows:
        print(
            f"{row['id']:<6}"
            f"{str(row['raw_uid'] or ''):<10}"
            f"{str(row['raw_user_id'] or ''):<15}"
            f"{str(row['raw_timestamp'] or ''):<24}"
            f"{str(row['normalized_uid'] or ''):<10}"
            f"{str(row['normalized_user_id'] or ''):<12}"
            f"{str(row['is_valid_timestamp']):<8}"
            f"{str(row['is_ready_for_api']):<8}"
            f"{str(row['normalization_notes'] or ''):<40}"
        )

    print("=" * 180)
    print(f"Total raw rows shown: {len(rows)}")


if __name__ == "__main__":
    main()