"""
HTTP client for Laravel attendance API.
"""

from __future__ import annotations

from typing import Dict, List

import requests
from loguru import logger

from config import (
    API_BASE_URL,
    API_ENDPOINT,
    API_TOKEN,
    DEVICE_SECRET,
    HTTP_TIMEOUT_SECONDS,
    SITE_ID,
)


def send_attendance_batch(records: List[Dict]) -> Dict:
    if not API_TOKEN:
        raise RuntimeError("API_TOKEN is missing in .env")

    if not SITE_ID:
        raise RuntimeError("SITE_ID is missing in .env")

    if not DEVICE_SECRET:
        raise RuntimeError("DEVICE_SECRET is missing in .env")

    if not records:
        return {"status": "ok", "accepted": []}

    top_device_sn = str(records[0]["device_sn"])

    url = f"{API_BASE_URL.rstrip('/')}/{API_ENDPOINT.lstrip('/')}"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "site_id": SITE_ID,
        "device_sn": top_device_sn,
        "device_secret": DEVICE_SECRET,
        "records": records,
    }

    logger.info("Sending {} attendance records to {}", len(records), url)

    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=HTTP_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    data = response.json()
    logger.success("Laravel accepted attendance batch")
    return data