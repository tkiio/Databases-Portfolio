"""Rebuild the analytical copy from SQLite, optionally checking before publication.

uv run python Module06a/refresh.py --check
uv run python Module06a/refresh.py --check-only
"""
import argparse
import csv
import math
import os
import sqlite3
import tempfile
import time
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent


def literal(path):
    return "'" + str(path).replace("'", "''") + "'"


def parquet_totals(con, path):
    return con.execute("SELECT COUNT(*), COALESCE(SUM(part_price),0) FROM read_parquet(?)",
                       [str(path)]).fetchone()


def check(expected, actual):
    print(f"SQLite rows={expected[0]} sum={expected[1]:.2f}")
    print(f"Parquet rows={actual[0]} sum={actual[1]:.2f}")
    matches = expected[0] == actual[0] and math.isclose(expected[1], actual[1], rel_tol=0, abs_tol=1e-6)
    print("check:", "PASS" if matches else "FAIL")
    return matches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    parser.add_argument("--db", type=Path, default=HERE / "history.db")
    parser.add_argument("--parquet", type=Path, default=HERE / "report_history.parquet")
    args = parser.parse_args()
    started = time.perf_counter()
    source = sqlite3.connect(args.db.resolve().as_uri() + "?mode=ro", uri=True)
    con = duckdb.connect()
    try:
        source.execute("BEGIN")  # counts and exported rows share one SQLite snapshot
        expected = source.execute("SELECT COUNT(*),COALESCE(SUM(part_price),0) FROM report_history").fetchone()
        if args.check_only:
            return 0 if check(expected, parquet_totals(con, args.parquet)) else 1
        # Local CSV bridge avoids downloading a SQLite extension. The temporary
        # Parquet is on the destination filesystem so os.replace is atomic.
        with tempfile.TemporaryDirectory(prefix="refresh-", dir=args.parquet.parent) as folder:
            folder = Path(folder)
            csv_path = folder / "snapshot.csv"
            pending = folder / "snapshot.parquet"
            cursor = source.execute("SELECT job_id,machine_id,site,technician,part_no,part_price,done_on FROM report_history")
            with csv_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(col[0] for col in cursor.description)
                writer.writerows(cursor)
            con.execute(f"""COPY (
                SELECT * FROM read_csv({literal(csv_path)}, header=true,
                columns={{'job_id':'BIGINT','machine_id':'VARCHAR','site':'VARCHAR',
                         'technician':'VARCHAR','part_no':'VARCHAR','part_price':'DOUBLE','done_on':'DATE'}})
                ) TO {literal(pending)} (FORMAT parquet, COMPRESSION snappy)""")
            actual = parquet_totals(con, pending)
            if args.check and not check(expected, actual):
                return 1  # preserve the existing report on a failed check
            os.replace(pending, args.parquet)
        print(f"rows={actual[0]} checksum_sum={actual[1]:.2f} parquet_bytes={args.parquet.stat().st_size} "
              f"elapsed_ms={(time.perf_counter()-started)*1000:.1f}")
        return 0
    finally:
        source.close()
        con.close()


if __name__ == "__main__":
    raise SystemExit(main())
