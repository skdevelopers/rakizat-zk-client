"""
Database helpers for local attendance pipeline.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from storage.schema import ensure_schema


def get_db(db_path: str) -> sqlite3.Connection:
    """
    Open SQLite connection.
    """
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL;")
    db.execute("PRAGMA synchronous=NORMAL;")
    db.execute("PRAGMA foreign_keys=ON;")
    ensure_schema(db)
    return db


def insert_raw_event(
    db_path: str,
    *,
    device_name: Optional[str],
    device_ip: str,
    device_sn: str,
    raw_uid: str | None,
    raw_user_id: str | None,
    raw_timestamp: str | None,
    raw_status: str | None,
    raw_punch: str | None,
    normalized_uid: int | None,
    normalized_user_id: int | None,
    normalized_timestamp: str | None,
    normalized_status: int | None,
    normalized_punch: int | None,
    is_numeric_user_id: bool,
    is_valid_timestamp: bool,
    is_ready_for_api: bool,
    normalization_notes: str | None,
) -> int:
    """
    Insert every device event into raw_events and return row ID.
    """
    db = get_db(db_path)
    try:
        cur = db.cursor()
        cur.execute("""
            INSERT INTO raw_events (
                device_name,
                device_ip,
                device_sn,
                raw_uid,
                raw_user_id,
                raw_timestamp,
                raw_status,
                raw_punch,
                normalized_uid,
                normalized_user_id,
                normalized_timestamp,
                normalized_status,
                normalized_punch,
                is_numeric_user_id,
                is_valid_timestamp,
                is_ready_for_api,
                normalization_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            device_name,
            device_ip,
            device_sn,
            raw_uid,
            raw_user_id,
            raw_timestamp,
            raw_status,
            raw_punch,
            normalized_uid,
            normalized_user_id,
            normalized_timestamp,
            normalized_status,
            normalized_punch,
            1 if is_numeric_user_id else 0,
            1 if is_valid_timestamp else 0,
            1 if is_ready_for_api else 0,
            normalization_notes,
        ))
        db.commit()
        return int(cur.lastrowid)
    finally:
        db.close()


def insert_outbox_record(
    db_path: str,
    *,
    raw_event_id: int,
    device_name: Optional[str],
    device_ip: str,
    device_sn: str,
    uid: int,
    user_id: int,
    timestamp: str,
    status: int,
    punch: int,
) -> bool:
    """
    Insert normalized event into attendance_outbox.

    Returns:
        True if inserted, False if duplicate.
    """
    db = get_db(db_path)
    try:
        cur = db.cursor()
        cur.execute("""
            INSERT OR IGNORE INTO attendance_outbox (
                raw_event_id,
                device_name,
                device_ip,
                device_sn,
                uid,
                user_id,
                timestamp,
                status,
                punch,
                sent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            raw_event_id,
            device_name,
            device_ip,
            device_sn,
            uid,
            user_id,
            timestamp,
            status,
            punch,
        ))
        db.commit()
        return cur.rowcount > 0
    finally:
        db.close()


def get_unsent_records(db_path: str, limit: int = 200) -> List[Dict[str, Any]]:
    """
    Fetch unsent normalized rows for API push.
    """
    db = get_db(db_path)
    try:
        cur = db.cursor()
        cur.execute("""
            SELECT
                id,
                raw_event_id,
                device_name,
                device_ip,
                device_sn,
                uid,
                user_id,
                timestamp,
                status,
                punch,
                sent,
                created_at,
                sent_at
            FROM attendance_outbox
            WHERE sent = 0
            ORDER BY timestamp ASC, id ASC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cur.fetchall()]
    finally:
        db.close()


def get_recent_raw_events(db_path: str, limit: int = 200) -> List[Dict[str, Any]]:
    db = get_db(db_path)
    try:
        cur = db.cursor()
        cur.execute("""
            SELECT *
            FROM raw_events
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cur.fetchall()]
    finally:
        db.close()


def get_recent_outbox_records(db_path: str, limit: int = 200) -> List[Dict[str, Any]]:
    db = get_db(db_path)
    try:
        cur = db.cursor()
        cur.execute("""
            SELECT *
            FROM attendance_outbox
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cur.fetchall()]
    finally:
        db.close()


def mark_records_sent(db_path: str, ids: List[int], api_response: str | None = None) -> None:
    """
    Mark normalized rows as sent after successful API call.
    """
    if not ids:
        return

    db = get_db(db_path)
    try:
        placeholders = ",".join("?" for _ in ids)
        params = [datetime.utcnow().isoformat(), api_response or ""] + ids
        db.execute(f"""
            UPDATE attendance_outbox
            SET sent = 1,
                sent_at = ?,
                api_response = ?
            WHERE id IN ({placeholders})
        """, params)
        db.commit()
    finally:
        db.close()