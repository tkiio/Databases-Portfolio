"""Compare the same normalized/report dashboard in a temporary DuckDB file.

Run after the main Module 5 setup. CSV export/COPY is outside the timed
region and uses no SQLite extension or network downloads. Source SQLite
data is opened read-only. Temporary CSV and DuckDB files are removed.
"""
import argparse
import csv
import math
import platform
import sqlite3
import statistics
import sys
import tempfile
import time
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import duckdb


HERE = Path(__file__).resolve().parent
REPEATS = 5

# site is explicitly grouped for portable SQL. Because machine_id -> site
# holds, this returns the same groups as the handout's SQLite query.
NORMALIZED = """
SELECT m.machine_id, m.site, j.technician, SUM(p.part_price) AS cost
FROM job AS j
JOIN machine AS m ON m.machine_id = j.machine_id
JOIN job_part AS jp ON jp.job_id = j.job_id
JOIN part AS p ON p.part_no = jp.part_no
WHERE j.done_on >= '2026-03-01'
GROUP BY m.machine_id, m.site, j.technician
"""

REPORT = """
SELECT machine_id, site, technician, SUM(part_price) AS cost
FROM report_jobpart
WHERE done_on >= '2026-03-01'
GROUP BY machine_id, site, technician
"""

TABLES = {
    "machine": (
        "machine_id, site",
        "machine_id VARCHAR PRIMARY KEY, site VARCHAR NOT NULL",
    ),
    "part": (
        "part_no, part_price",
        "part_no VARCHAR PRIMARY KEY, part_price DOUBLE NOT NULL",
    ),
    "job": (
        "job_id, machine_id, technician, done_on",
        "job_id BIGINT PRIMARY KEY, machine_id VARCHAR NOT NULL, "
        "technician VARCHAR NOT NULL, done_on VARCHAR NOT NULL",
    ),
    "job_part": (
        "job_id, part_no",
        "job_id BIGINT NOT NULL, part_no VARCHAR NOT NULL, "
        "PRIMARY KEY(job_id, part_no)",
    ),
    "report_jobpart": (
        "job_id, machine_id, site, technician, part_no, part_price, done_on",
        "job_id BIGINT, machine_id VARCHAR, site VARCHAR, technician VARCHAR, "
        "part_no VARCHAR, part_price DOUBLE, done_on VARCHAR",
    ),
}


def equivalent(left, right):
    left, right = sorted(left), sorted(right)
    assert len(left) == len(right), (len(left), len(right))
    for a, b in zip(left, right):
        assert a[:-1] == b[:-1], (a, b)
        assert math.isclose(a[-1], b[-1], rel_tol=1e-12, abs_tol=1e-8), (a, b)


def load(sqlite_conn, duck_conn, folder):
    for table, (columns, schema) in TABLES.items():
        duck_conn.execute(f"CREATE TABLE {table}({schema})")
        path = folder / f"{table}.csv"
        cursor = sqlite_conn.execute(f"SELECT {columns} FROM {table}")
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(col[0] for col in cursor.description)
            writer.writerows(cursor)
        # Identifier names come only from TABLES. The pathname is a SQL string
        # literal, so apostrophes must be doubled instead of shell-escaped.
        literal = "'" + str(path).replace("'", "''") + "'"
        duck_conn.execute(f"COPY {table} FROM {literal} (FORMAT CSV, HEADER TRUE)")
        source = sqlite_conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        copied = duck_conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert source == copied, (table, source, copied)
        print(f"Copied {table}: {copied} rows")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=HERE / "normalize.db")
    args = parser.parse_args()
    uri = args.db.resolve().as_uri() + "?mode=ro"
    print("Optional DuckDB dashboard comparison")
    print("Measured UTC:", datetime.now(timezone.utc).isoformat())
    print("Python:", sys.version.split()[0], "DuckDB:", duckdb.__version__)
    print("Source SQLite library:", sqlite3.sqlite_version)
    print("Platform:", platform.system(), platform.machine())
    print("Date columns stay VARCHAR; ISO date comparisons match the SQLite fixture.")
    print("Grouping includes site explicitly for portable SQL.")
    print("Both engines are checked against the same source rows and report values.")

    with closing(sqlite3.connect(uri, uri=True)) as source:
        expected = source.execute(NORMALIZED).fetchall()
        equivalent(expected, source.execute(REPORT).fetchall())
        with tempfile.TemporaryDirectory(prefix="module05-duckdb-") as folder_name:
            folder = Path(folder_name)
            with closing(duckdb.connect(str(folder / "comparison.duckdb"))) as conn:
                # SQLite executes a query on one thread; avoid crediting a
                # multithreading advantage to columnar storage in this test.
                conn.execute("SET threads=1")
                print("DuckDB worker threads:", conn.execute("SELECT current_setting('threads')").fetchone()[0])
                load(source, conn, folder)
                queries = {"normalized": NORMALIZED, "report": REPORT}
                for name, query in queries.items():
                    print(f"\n{name.upper()} SQL:\n{query.strip()};")
                    print("EXPLAIN:")
                    for row in conn.execute("EXPLAIN " + query).fetchall():
                        print(row[-1])
                    equivalent(expected, conn.execute(query).fetchall())  # warm-up

                timings = {name: [] for name in queries}
                for repeat in range(REPEATS):
                    order = ("normalized", "report") if repeat % 2 == 0 else ("report", "normalized")
                    for name in order:
                        begin = time.perf_counter()
                        rows = conn.execute(queries[name]).fetchall()
                        elapsed = time.perf_counter() - begin
                        equivalent(expected, rows)  # verification is outside the timer
                        timings[name].append(elapsed)
                print("\nTIMING METHOD")
                print("One untimed warm-up for each query; five alternating measured pairs.")
                print("Wall-clock perf_counter includes query execution and fetching every result row.")
                print("Import/COPY, schema setup, connection creation and checks are excluded.")
                print("DuckDB tables have primary keys; no extra dashboard indexes were added.")
                print("Result rows:", len(expected))
                print("Total report cost:", sum(row[-1] for row in expected))
                for name, values in timings.items():
                    print(f"{name} runs_ms:", ", ".join(f"{v * 1000:.3f}" for v in values))
                    print(f"{name} median_ms: {statistics.median(values) * 1000:.3f}")
                ratio = statistics.median(timings["normalized"]) / statistics.median(timings["report"])
                print(f"normalized/report median ratio: {ratio:.3f}x")
                print("All measured results matched the source SQLite output.")
                print("This dataset can show a local read trade-off; it cannot establish that")
                print("DuckDB removes every production need for denormalization or faster refreshes.")


if __name__ == "__main__":
    main()
