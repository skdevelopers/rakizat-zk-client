#!/usr/bin/env python3
"""
SQLite attendance buffer inspector and optional cleaner.

Usage:
    python3 tools/view_attendance_sqlite.py

This script is SAFE by default:
- it only reads and reports
- delete operations are disabled unless explicitly enabled

Target DB:
    /home/skdev/zkclient/attendance.sqlite3
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


DB_PATH = Path("/home/skdev/zkclient/attendance.sqlite3")
TABLE_NAME = "attendance_buffer"

# Safety switch:
# Keep False for read-only mode.
ENABLE_DELETE = False

# If you later want to remove obvious junk rows, keep these targeted only.
DELETE_RULES = {
    "delete_year_2000_rows": False,
    "delete_empty_user_rows": False,
    "delete_exact_duplicates_keep_lowest_id": False,
}


def print_title(title: str) -> None:
    """Print a formatted section title."""
    print("\n" + "=" * 110)
    print(title)
    print("=" * 110)


def connect_db(db_path: Path) -> sqlite3.Connection:
    """Create SQLite connection."""
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def fetch_all(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    """Fetch all rows for a query."""
    cur = conn.execute(sql, params)
    return cur.fetchall()


def fetch_one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
    """Fetch one row for a query."""
    cur = conn.execute(sql, params)
    return cur.fetchone()


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    """Check whether the target table exists."""
    row = fetch_one(
        conn,
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (table_name,),
    )
    return row is not None


def get_columns(conn: sqlite3.Connection, table_name: str) -> list[sqlite3.Row]:
    """Return PRAGMA table_info for the table."""
    return fetch_all(conn, f"PRAGMA table_info({table_name})")


def show_schema(conn: sqlite3.Connection) -> None:
    """Display table schema."""
    print_title("TABLE SCHEMA")
    columns = get_columns(conn, TABLE_NAME)

    if not columns:
        print("No columns found.")
        return

    print(f"{'cid':<5} {'name':<25} {'type':<20} {'notnull':<8} {'default':<20} {'pk':<5}")
    print("-" * 110)
    for col in columns:
        print(
            f"{col['cid']:<5} "
            f"{str(col['name']):<25} "
            f"{str(col['type']):<20} "
            f"{col['notnull']:<8} "
            f"{str(col['dflt_value']):<20} "
            f"{col['pk']:<5}"
        )


def show_basic_counts(conn: sqlite3.Connection) -> None:
    """Display basic row counts."""
    print_title("BASIC COUNTS")

    total = fetch_one(conn, f"SELECT COUNT(*) AS c FROM {TABLE_NAME}")
    print(f"Total rows: {total['c'] if total else 0}")

    if column_exists(conn, TABLE_NAME, "sent"):
        sent_counts = fetch_all(
            conn,
            f"""
            SELECT sent, COUNT(*) AS c
            FROM {TABLE_NAME}
            GROUP BY sent
            ORDER BY sent
            """
        )
        print("\nCounts by sent:")
        for row in sent_counts:
            print(f"  sent={row['sent']}: {row['c']}")

    if column_exists(conn, TABLE_NAME, "status"):
        status_counts = fetch_all(
            conn,
            f"""
            SELECT status, COUNT(*) AS c
            FROM {TABLE_NAME}
            GROUP BY status
            ORDER BY status
            """
        )
        print("\nCounts by status:")
        for row in status_counts:
            print(f"  status={row['status']}: {row['c']}")

    if column_exists(conn, TABLE_NAME, "punch"):
        punch_counts = fetch_all(
            conn,
            f"""
            SELECT punch, COUNT(*) AS c
            FROM {TABLE_NAME}
            GROUP BY punch
            ORDER BY punch
            """
        )
        print("\nCounts by punch:")
        for row in punch_counts:
            print(f"  punch={row['punch']}: {row['c']}")


def column_exists(conn: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    columns = get_columns(conn, table_name)
    return any(col["name"] == column_name for col in columns)


def show_sample_rows(conn: sqlite3.Connection) -> None:
    """Show oldest and latest rows."""
    print_title("SAMPLE ROWS")

    order_column = "id" if column_exists(conn, TABLE_NAME, "id") else "rowid"

    print("\nOldest 10 rows:")
    rows = fetch_all(conn, f"SELECT * FROM {TABLE_NAME} ORDER BY {order_column} ASC LIMIT 10")
    for row in rows:
        print(dict(row))

    print("\nLatest 10 rows:")
    rows = fetch_all(conn, f"SELECT * FROM {TABLE_NAME} ORDER BY {order_column} DESC LIMIT 10")
    for row in rows:
        print(dict(row))


def show_timestamp_issues(conn: sqlite3.Connection) -> None:
    """Report suspicious timestamp values."""
    if not column_exists(conn, TABLE_NAME, "timestamp"):
        return

    print_title("TIMESTAMP HEALTH CHECK")

    rules = [
        ("Year 2000 placeholder", "timestamp LIKE '2000-%'"),
        ("Very old dates (< 2010)", "timestamp < '2010-01-01'"),
        ("Far future dates (> 2035)", "timestamp > '2035-01-01'"),
        ("Null timestamp", "timestamp IS NULL"),
        ("Empty timestamp", "TRIM(timestamp) = ''"),
    ]

    for label, where_clause in rules:
        row = fetch_one(
            conn,
            f"""
            SELECT COUNT(*) AS c
            FROM {TABLE_NAME}
            WHERE {where_clause}
            """
        )
        print(f"{label:<35}: {row['c'] if row else 0}")

    print("\nSample suspicious rows:")
    bad_rows = fetch_all(
        conn,
        f"""
        SELECT *
        FROM {TABLE_NAME}
        WHERE timestamp LIKE '2000-%'
           OR timestamp < '2010-01-01'
           OR timestamp > '2035-01-01'
           OR timestamp IS NULL
           OR TRIM(timestamp) = ''
        ORDER BY id DESC
        LIMIT 20
        """
    )
    for row in bad_rows:
        print(dict(row))


def show_empty_field_issues(conn: sqlite3.Connection) -> None:
    """Report empty user or device identifiers."""
    print_title("EMPTY FIELD CHECKS")

    checks: list[tuple[str, str]] = []

    if column_exists(conn, TABLE_NAME, "user_id"):
        checks.append(("Empty/null user_id", "user_id IS NULL OR TRIM(CAST(user_id AS TEXT)) = ''"))

    if column_exists(conn, TABLE_NAME, "device_sn"):
        checks.append(("Empty/null device_sn", "device_sn IS NULL OR TRIM(device_sn) = ''"))

    if column_exists(conn, TABLE_NAME, "device_ip"):
        checks.append(("Empty/null device_ip", "device_ip IS NULL OR TRIM(device_ip) = ''"))

    if not checks:
        print("No relevant columns found for empty-field checks.")
        return

    for label, where_clause in checks:
        row = fetch_one(conn, f"SELECT COUNT(*) AS c FROM {TABLE_NAME} WHERE {where_clause}")
        print(f"{label:<35}: {row['c'] if row else 0}")


def show_duplicates(conn: sqlite3.Connection) -> None:
    """Detect likely duplicate attendance logs."""
    print_title("DUPLICATE DETECTION")

    needed = ["user_id", "device_sn", "timestamp"]
    if not all(column_exists(conn, TABLE_NAME, col) for col in needed):
        print("Duplicate check skipped: user_id, device_sn, timestamp columns are required.")
        return

    rows = fetch_all(
        conn,
        f"""
        SELECT
            user_id,
            device_sn,
            timestamp,
            COUNT(*) AS dup_count,
            GROUP_CONCAT(id) AS ids
        FROM {TABLE_NAME}
        GROUP BY user_id, device_sn, timestamp
        HAVING COUNT(*) > 1
        ORDER BY dup_count DESC, timestamp DESC
        LIMIT 50
        """
    )

    if not rows:
        print("No exact duplicates found on (user_id, device_sn, timestamp).")
        return

    print(f"Found {len(rows)} duplicate groups.\n")
    for row in rows:
        print(
            f"user_id={row['user_id']}, "
            f"device_sn={row['device_sn']}, "
            f"timestamp={row['timestamp']}, "
            f"dup_count={row['dup_count']}, "
            f"ids={row['ids']}"
        )

    total_dup_rows = fetch_one(
        conn,
        f"""
        SELECT COALESCE(SUM(dup_count - 1), 0) AS extra_rows
        FROM (
            SELECT COUNT(*) AS dup_count
            FROM {TABLE_NAME}
            GROUP BY user_id, device_sn, timestamp
            HAVING COUNT(*) > 1
        ) t
        """
    )
    print(f"\nExtra duplicate rows removable: {total_dup_rows['extra_rows'] if total_dup_rows else 0}")


def delete_obvious_junk(conn: sqlite3.Connection) -> None:
    """Delete only explicitly enabled junk rows."""
    if not ENABLE_DELETE:
        print_title("DELETE MODE")
        print("Delete mode is OFF. No rows were removed.")
        return

    print_title("DELETE MODE")

    if DELETE_RULES["delete_year_2000_rows"] and column_exists(conn, TABLE_NAME, "timestamp"):
        cur = conn.execute(
            f"""
            DELETE FROM {TABLE_NAME}
            WHERE timestamp LIKE '2000-%'
            """
        )
        print(f"Deleted year-2000 rows: {cur.rowcount}")

    if DELETE_RULES["delete_empty_user_rows"] and column_exists(conn, TABLE_NAME, "user_id"):
        cur = conn.execute(
            f"""
            DELETE FROM {TABLE_NAME}
            WHERE user_id IS NULL OR TRIM(CAST(user_id AS TEXT)) = ''
            """
        )
        print(f"Deleted empty user rows: {cur.rowcount}")

    if DELETE_RULES["delete_exact_duplicates_keep_lowest_id"]:
        needed = ["id", "user_id", "device_sn", "timestamp"]
        if all(column_exists(conn, TABLE_NAME, col) for col in needed):
            cur = conn.execute(
                f"""
                DELETE FROM {TABLE_NAME}
                WHERE id IN (
                    SELECT id
                    FROM (
                        SELECT id,
                               ROW_NUMBER() OVER (
                                   PARTITION BY user_id, device_sn, timestamp
                                   ORDER BY id ASC
                               ) AS rn
                        FROM {TABLE_NAME}
                    ) x
                    WHERE x.rn > 1
                )
                """
            )
            print(f"Deleted exact duplicate rows: {cur.rowcount}")

    conn.commit()
    print("Delete actions committed.")


def vacuum_db(conn: sqlite3.Connection) -> None:
    """Run VACUUM only when delete mode is enabled."""
    if not ENABLE_DELETE:
        return

    print_title("VACUUM")
    conn.execute("VACUUM")
    print("VACUUM completed.")


def main() -> None:
    """Run inspection workflow."""
    print_title("SQLITE ATTENDANCE BUFFER INSPECTOR")
    print(f"DB Path    : {DB_PATH}")
    print(f"Table Name : {TABLE_NAME}")

    conn = connect_db(DB_PATH)
    try:
        if not table_exists(conn, TABLE_NAME):
            raise RuntimeError(f"Table '{TABLE_NAME}' not found in database.")

        show_schema(conn)
        show_basic_counts(conn)
        show_sample_rows(conn)
        show_timestamp_issues(conn)
        show_empty_field_issues(conn)
        show_duplicates(conn)
        delete_obvious_junk(conn)
        vacuum_db(conn)
    finally:
        conn.close()

    print_title("DONE")


if __name__ == "__main__":
    main()