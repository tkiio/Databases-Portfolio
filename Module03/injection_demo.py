"""Demonstrate an apostrophe crash and the safe bound-parameter fix."""

import sqlite3
from pathlib import Path

DB = Path(__file__).with_name("warehouse.db")
if not DB.exists():
    raise SystemExit(f"{DB} not found — run the Module 3 setup first")


def vulnerable(conn: sqlite3.Connection, name: str):
    """Don't do this: interpolating a value lets it become SQL syntax."""
    sql = f"SELECT customer_id, name FROM customer WHERE name = '{name}'"
    return conn.execute(sql).fetchall()


def safe(conn: sqlite3.Connection, name: str):
    """Bind the value separately so it is treated as data, not SQL."""
    sql = "SELECT customer_id, name FROM customer WHERE name = ?"
    return conn.execute(sql, (name,)).fetchall()


if __name__ == "__main__":
    with sqlite3.connect(DB) as conn:
        print("normal   :", vulnerable(conn, "Customer 1"))
        try:
            print("apostrophe:", vulnerable(conn, "O'Neil"))
        except sqlite3.Error as exc:
            print("apostrophe: crashed with", exc)
        print("apostrophe safe:", safe(conn, "O'Neil"))
        payload = "' OR '1'='1"
        try:
            print("injected :", vulnerable(conn, payload)[:3], "...")
        except sqlite3.Error as exc:
            print("injected : crashed with", exc)
        print("safe     :", safe(conn, payload))
