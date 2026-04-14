"""
Run one attendance pull from all configured devices.
"""

from __future__ import annotations

import tools._bootstrap  # noqa: F401

from config import DB_PATH, DEVICES
from core.device_sync import process_device


def main() -> None:
    """
    Pull logs from all configured devices once.
    """
    if not DEVICES:
        print("No devices configured in .env")
        return

    for device in DEVICES:
        process_device(device, DB_PATH)

    print("Device pull test completed.")


if __name__ == "__main__":
    main()