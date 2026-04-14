"""
SQLite schema helpers.
"""

from __future__ import annotations

from sqlite3 import Connection


def ensure_schema(db: Connection) -> None:
    """
    Ensure required tables and indexes exist.
    """
    db.execute("""
        CREATE TABLE IF NOT EXISTS raw_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name TEXT NULL,
            device_ip TEXT NOT NULL,
            device_sn TEXT NOT NULL,
            raw_uid TEXT NULL,
            raw_user_id TEXT NULL,
            raw_timestamp TEXT NULL,
            raw_status TEXT NULL,
            raw_punch TEXT NULL,
            normalized_uid INTEGER NULL,
            normalized_user_id INTEGER NULL,
            normalized_timestamp TEXT NULL,
            normalized_status INTEGER NULL,
            normalized_punch INTEGER NULL,
            is_numeric_user_id INTEGER NOT NULL DEFAULT 0,
            is_valid_timestamp INTEGER NOT NULL DEFAULT 0,
            is_ready_for_api INTEGER NOT NULL DEFAULT 0,
            normalization_notes TEXT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_raw_events_device_created
        ON raw_events (device_sn, created_at)
    """)

    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_raw_events_ready
        ON raw_events (is_ready_for_api, created_at)
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS attendance_outbox (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_event_id INTEGER NOT NULL,
            device_name TEXT NULL,
            device_ip TEXT NOT NULL,
            device_sn TEXT NOT NULL,
            uid INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            status INTEGER NOT NULL DEFAULT 0,
            punch INTEGER NOT NULL DEFAULT 0,
            sent INTEGER NOT NULL DEFAULT 0,
            sent_at TEXT NULL,
            api_response TEXT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY(raw_event_id) REFERENCES raw_events(id) ON DELETE CASCADE
        )
    """)

    db.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_attendance_outbox_unique_log
        ON attendance_outbox (device_sn, user_id, timestamp, punch)
    """)

    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_attendance_outbox_sent
        ON attendance_outbox (sent, timestamp)
    """)

    db.commit()