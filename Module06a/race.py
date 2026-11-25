# Module06a/race.py — run with:  uv run python Module06a/race.py
"""Same two queries, two engines, interleaved, median of RUNS runs."""
import sqlite3
import statistics
import time
import json
import math
from pathlib import Path

import duckdb

RUNS = 5        # odd on purpose: the median is then a real run. Try 3, 7, 9.

here = Path(__file__).parent
sq = sqlite3.connect((here / "history.db").resolve().as_uri() + "?mode=ro", uri=True)
duck = duckdb.connect()
pq = str(here / "report_history.parquet")

DASHBOARD = """SELECT machine_id, site, technician, SUM(part_price) AS cost
FROM {src} WHERE done_on >= '2026-01-01'
GROUP BY machine_id, site, technician"""

MONTHLY = """SELECT strftime('%Y-%m', done_on) AS month, machine_id,
       COUNT(*) AS part_rows, SUM(part_price) AS cost
FROM {src} GROUP BY month, machine_id ORDER BY month, machine_id"""


def timed_ms(fn):
    t0 = time.perf_counter()
    fn()
    return (time.perf_counter() - t0) * 1000


def spread(times):
    return f"{min(times):.1f}-{max(times):.1f}"


results = {}
for name, sql in (("dashboard", DASHBOARD), ("monthly", MONTHLY)):
    run_sqlite = lambda: sq.execute(sql.format(src="report_history")).fetchall()
    run_duckdb = lambda: duck.execute(sql.format(src=f"read_parquet('{pq}')")).fetchall()

    a, b = sorted(run_sqlite()), sorted(run_duckdb())  # warm-up and check
    assert len(a) == len(b)
    for left, right in zip(a, b):
        assert left[:-1] == right[:-1]
        assert math.isclose(left[-1], right[-1], rel_tol=1e-12, abs_tol=1e-6)

    sqlite_times, duckdb_times = [], []
    for i in range(RUNS):
        # Change which engine runs first, rather than always giving it to SQLite.
        cases = [(run_sqlite, sqlite_times), (run_duckdb, duckdb_times)]
        for fn, times in (cases if i % 2 == 0 else reversed(cases)):
            times.append(timed_ms(fn))

    s = statistics.median(sqlite_times)
    d = statistics.median(duckdb_times)
    print(f"{name:10s} sqlite {s:7.1f} ms [{spread(sqlite_times)}]"
          f"   duckdb {d:6.1f} ms [{spread(duckdb_times)}]   {s / d:6.1f}x")
    results[name] = {"sqlite_runs_ms": sqlite_times, "duckdb_runs_ms": duckdb_times,
                     "sqlite_median_ms": s, "duckdb_median_ms": d,
                     "speedup": s / d, "result_rows": len(a),
                     "result_cost": sum(row[-1] for row in a)}
print("Both engines returned matching answers. Monthly COUNT(*) counts part rows.")
print("Versions: SQLite", sqlite3.sqlite_version, "DuckDB", duckdb.__version__)
(here / "evidence").mkdir(exist_ok=True)
(here / "evidence/race.json").write_text(json.dumps(results, indent=2) + "\n")
sq.close()
duck.close()
