"""
Pull logs from device, preserve raw attempts, and prepare valid outbox rows.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict

from loguru import logger

from network.health import tcp_check
from network.zk_client import connect_device
from storage.db import insert_outbox_record, insert_raw_event


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_int(value: Any) -> int | None:
    try:
        return int(str(value).strip())
    except Exception:
        return None


def _normalize_numeric_user_id(raw_user_id: Any) -> int | None:
    text = _safe_str(raw_user_id)
    if not text:
        return None
    if not text.isdigit():
        return None
    return int(text)


def _normalize_timestamp(value: Any) -> tuple[str | None, bool]:
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).strip())
        except Exception:
            return None, False

    parsed = parsed.replace(microsecond=0)

    now = datetime.now()
    min_dt = now - timedelta(days=120)
    max_dt = now + timedelta(hours=12)

    if parsed < min_dt or parsed > max_dt:
        return parsed.isoformat(), False

    return parsed.isoformat(), True


def process_device(device: Dict[str, Any], db_path: str) -> None:
    ip = str(device["ip"]).strip()
    port = int(device.get("port", 4370))
    key = int(device.get("comm_key", 0))
    name = str(device.get("name", "")).strip() or None

    if not tcp_check(ip, port):
        logger.warning("Device unreachable | name={} | ip={}:{}", name, ip, port)
        return

    conn = None
    raw_saved = 0
    outbox_inserted = 0
    outbox_duplicates = 0
    invalid_rows = 0

    try:
        conn = connect_device(ip, port, key)
        sn = str(conn.get_serialnumber()).strip()
        records = conn.get_attendance()

        for record in records:
            raw_uid = _safe_str(getattr(record, "uid", None))
            raw_user_id = _safe_str(getattr(record, "user_id", None))
            raw_timestamp = _safe_str(getattr(record, "timestamp", None))
            raw_status = _safe_str(getattr(record, "status", None))
            raw_punch = _safe_str(getattr(record, "punch", None))

            normalized_uid = _normalize_int(getattr(record, "uid", None))
            normalized_user_id = _normalize_numeric_user_id(getattr(record, "user_id", None))
            normalized_status = _normalize_int(getattr(record, "status", 0))
            normalized_punch = _normalize_int(getattr(record, "punch", 0))
            normalized_timestamp, is_valid_timestamp = _normalize_timestamp(
                getattr(record, "timestamp", None)
            )

            is_numeric_user_id = normalized_user_id is not None
            is_ready_for_api = (
                is_numeric_user_id
                and is_valid_timestamp
                and normalized_uid is not None
                and normalized_status is not None
                and normalized_punch is not None
            )

            notes = []
            if not is_numeric_user_id:
                notes.append("non_numeric_user_id")
            if not is_valid_timestamp:
                notes.append("invalid_timestamp")
            if normalized_uid is None:
                notes.append("invalid_uid")
            if normalized_status is None:
                notes.append("invalid_status")
            if normalized_punch is None:
                notes.append("invalid_punch")

            raw_event_id = insert_raw_event(
                db_path=db_path,
                device_name=name,
                device_ip=ip,
                device_sn=sn,
                raw_uid=raw_uid,
                raw_user_id=raw_user_id,
                raw_timestamp=raw_timestamp,
                raw_status=raw_status,
                raw_punch=raw_punch,
                normalized_uid=normalized_uid,
                normalized_user_id=normalized_user_id,
                normalized_timestamp=normalized_timestamp,
                normalized_status=normalized_status,
                normalized_punch=normalized_punch,
                is_numeric_user_id=is_numeric_user_id,
                is_valid_timestamp=is_valid_timestamp,
                is_ready_for_api=is_ready_for_api,
                normalization_notes=",".join(notes) if notes else None,
            )
            raw_saved += 1

            if not is_ready_for_api:
                invalid_rows += 1
                continue

            inserted = insert_outbox_record(
                db_path=db_path,
                raw_event_id=raw_event_id,
                device_name=name,
                device_ip=ip,
                device_sn=sn,
                uid=normalized_uid,
                user_id=normalized_user_id,
                timestamp=normalized_timestamp,
                status=normalized_status,
                punch=normalized_punch,
            )

            if inserted:
                outbox_inserted += 1
            else:
                outbox_duplicates += 1

        logger.success(
            "Device processed | name={} | sn={} | raw_saved={} | outbox_inserted={} | outbox_duplicates={} | invalid_rows={}",
            name,
            sn,
            raw_saved,
            outbox_inserted,
            outbox_duplicates,
            invalid_rows,
        )

    except Exception as exc:
        logger.exception("Device sync failed | name={} | ip={} | error={}", name, ip, exc)

    finally:
        if conn is not None:
            try:
                conn.enable_device()
            except Exception:
                pass
            try:
                conn.disconnect()
            except Exception:
                pass