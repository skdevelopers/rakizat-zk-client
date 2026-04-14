from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "attendance.sqlite3"))

SYNC_INTERVAL_MINUTES = int(os.getenv("SYNC_INTERVAL_MINUTES", "1"))
PULL_INTERVAL_SECONDS = int(os.getenv("PULL_INTERVAL_SECONDS", "15"))
HTTP_TIMEOUT_SECONDS = int(os.getenv("HTTP_TIMEOUT_SECONDS", "20"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "300"))

API_BASE_URL = os.getenv("API_BASE_URL", "")
API_ENDPOINT = os.getenv("API_ENDPOINT", "/api/attendance/ingest")
API_TOKEN = os.getenv("API_TOKEN", "")

SITE_ID = os.getenv("SITE_ID", "")
DEVICE_SECRET = os.getenv("DEVICE_SECRET", "")
DEVICE_TIME_PAST_DAYS = int(os.getenv("DEVICE_TIME_PAST_DAYS", "30"))
DEVICE_TIME_FUTURE_MINUTES = int(os.getenv("DEVICE_TIME_FUTURE_MINUTES", "10"))

RAW_DEVICES = os.getenv("DEVICES", "[]")
try:
    DEVICES = json.loads(RAW_DEVICES)
    if not isinstance(DEVICES, list):
        DEVICES = []
except Exception:
    DEVICES = []