"""Load the small synthetic readings.csv using bound parameters and UPSERT.

Run after setup and sensor seeding. Paths default to this script's folder.
Each CSV is one transaction: a rejected reading rolls back the whole file.
The course UPSERT updates value only; interval_s is unchanged on a replay.
"""
import argparse
import csv
import sqlite3
from contextlib import closing
from pathlib import Path

HERE = Path(__file__).resolve().parent
UPSERT = """
INSERT INTO reading(sensor_id, ts, value, interval_s) VALUES (?, ?, ?, ?)
ON CONFLICT(sensor_id, ts) DO UPDATE SET value = excluded.value
"""


def ingest(db: Path, csv_path: Path) -> tuple[int, int, int]:
    # mode=rw refuses to silently create an empty database at a mistyped path.
    with csv_path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        required = {"sensor_id", "ts", "value", "interval_s"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"CSV requires columns: {', '.join(sorted(required))}")
        # Keep SQLite responsible for type/domain validation. In particular,
        # int(1.5) would silently truncate, and float('NaN') is not a reading.
        rows = [(r["sensor_id"], r["ts"], r["value"], r["interval_s"]) for r in reader]

    with closing(sqlite3.connect(db.resolve().as_uri() + "?mode=rw", uri=True)) as conn:
        conn.execute("PRAGMA foreign_keys = ON")  # before the transaction
        if conn.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
            raise RuntimeError("Foreign-key enforcement could not be enabled")
        before = conn.execute("SELECT COUNT(*) FROM reading").fetchone()[0]
        with conn:
            conn.executemany(UPSERT, rows)
        after = conn.execute("SELECT COUNT(*) FROM reading").fetchone()[0]
    return len(rows), before, after


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, nargs="?", default=HERE / "readings.csv")
    parser.add_argument("--db", type=Path, default=HERE / "edge.db")
    args = parser.parse_args()
    processed, before, after = ingest(args.db, args.csv)
    print(f"Processed CSV rows: {processed}")
    print(f"Reading count before: {before}")
    print(f"Reading count after: {after}")


if __name__ == "__main__":
    main()
