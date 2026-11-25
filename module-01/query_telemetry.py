"""Read the local telemetry database with a bound vibration threshold."""

import argparse
import sqlite3
from contextlib import closing
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("threshold", type=float, nargs="?", default=2.0)
    args = parser.parse_args()

    database = Path(__file__).resolve().with_name("telemetry.db")
    if not database.is_file():
        parser.exit(1, "Build telemetry.db with load_telemetry.py first.\n")

    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as conn:
        count, = conn.execute(
            "SELECT COUNT(*) FROM readings WHERE vib_rms > ?",
            (args.threshold,),
        ).fetchone()
    print(f"{count:,} readings above {args.threshold:g} mm/s")


if __name__ == "__main__":
    main()
