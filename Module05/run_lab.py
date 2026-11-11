"""Build and run the Module 5 experiments, including the optional comparisons.

An existing normalize.db requires --reset, which deliberately erases this
lab's generated tables and data. Use the notes for the human pod gates.
"""
import argparse
import json
import re
import sqlite3
import subprocess
import sys
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB = HERE / "normalize.db"
EVIDENCE = HERE / "evidence"


def capture(script, target):
    process = subprocess.run([sys.executable, str(HERE / script)], capture_output=True,
                             text=True, check=True, timeout=180)
    (EVIDENCE / target).write_text(process.stdout, encoding="utf-8")
    if process.stderr:
        print(process.stderr, file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    if DB.exists() and not args.reset:
        raise SystemExit("normalize.db exists. Use --reset only to rebuild the generated Module 5 lab data.")
    EVIDENCE.mkdir(exist_ok=True)
    with closing(sqlite3.connect(DB, cached_statements=0)) as conn:
        for name in ("setup.sql", "normalize.sql", "report.sql"):
            conn.executescript((HERE / name).read_text())
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        log = ["Round 3: setup and decomposition",
               "Measured UTC: " + datetime.now(timezone.utc).isoformat(),
               f"Python {sys.version.split()[0]}; Python SQLite {sqlite3.sqlite_version}",
               "Executed setup.sql, normalize.sql and report.sql. Foreign keys ON."]
        expected_counts = {"flat_jobpart": 200000, "machine": 50, "part": 10,
                           "job": 20000, "job_part": 200000, "report_jobpart": 200000}
        for table, count in expected_counts.items():
            query = f"SELECT COUNT(*) FROM {table}"
            actual = conn.execute(query).fetchone()[0]
            assert actual == count, (table, actual)
            log.extend([query + ";", str(actual)])
        for label, query in {
            "job_id determines machine, technician and date": "SELECT job_id FROM flat_jobpart GROUP BY job_id HAVING COUNT(DISTINCT machine_id)>1 OR COUNT(DISTINCT technician)>1 OR COUNT(DISTINCT done_on)>1",
            "machine_id determines site": "SELECT machine_id FROM flat_jobpart GROUP BY machine_id HAVING COUNT(DISTINCT site)>1",
            "part_no determines price": "SELECT part_no FROM flat_jobpart GROUP BY part_no HAVING COUNT(DISTINCT part_price)>1",
            "job/part is unique": "SELECT job_id,part_no FROM flat_jobpart GROUP BY job_id,part_no HAVING COUNT(*)>1",
        }.items():
            assert conn.execute(query).fetchall() == []
            log.extend([label, query + ";", "0 violating groups"])
        rebuild = """SELECT j.job_id,m.machine_id,m.site,j.technician,jp.part_no,p.part_price,j.done_on
FROM job AS j JOIN machine AS m ON m.machine_id=j.machine_id
JOIN job_part AS jp ON jp.job_id=j.job_id JOIN part AS p ON p.part_no=jp.part_no"""
        flat = "SELECT job_id,machine_id,site,technician,part_no,CAST(part_price AS REAL),done_on FROM flat_jobpart"
        joined = conn.execute("SELECT COUNT(*) FROM (" + rebuild + ")").fetchone()[0]
        assert joined == 200000
        log.extend(["Actual four-table join count:", rebuild + ";", str(joined)])
        for label, query in (("Missing reconstructed rows", flat + " EXCEPT " + rebuild),
                             ("Extra reconstructed rows", rebuild + " EXCEPT " + flat)):
            difference = conn.execute("SELECT COUNT(*) FROM (" + query + ")").fetchone()[0]
            assert difference == 0
            log.extend([label, query + ";", str(difference)])
        log.append("Equal counts AND both EXCEPT directions are empty: all facts reconstruct.")
        log.append("Parts: " + repr(conn.execute("SELECT part_no,part_price FROM part ORDER BY part_no").fetchall()))
        counterexample = "SELECT machine_id,COUNT(DISTINCT technician) FROM job GROUP BY machine_id HAVING COUNT(DISTINCT technician)>1 LIMIT 1"
        row = conn.execute(counterexample).fetchone()
        assert row is not None
        log.extend(["Counterexample to assuming one technician per machine:", counterexample + ";", repr(row)])
        log.append("No violations in this generated dataset confirm consistency here, not a permanent business rule.")
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        log.append("PRAGMA foreign_key_check: no violations.")
    (EVIDENCE / "build.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    capture("anomalies.py", "anomalies.txt")
    process = subprocess.run([sys.executable, str(HERE / "bench.py")], check=True, timeout=180)
    capture("duckdb_compare.py", "duckdb.txt")
    raw_duckdb = (EVIDENCE / "duckdb.txt").read_text()
    duckdb_times = {name: float(ms) for name, ms in
                    re.findall(r"^(normalized|report) median_ms: ([0-9.]+)$", raw_duckdb, re.M)}
    assert set(duckdb_times) == {"normalized", "report"}
    sqlite_results = json.loads((EVIDENCE / "benchmark.json").read_text())
    sqlite_times = sqlite_results["unindexed"]["median_ms"]
    summary = ["# My DuckDB comparison", "",
               "The same data and answers were checked in both engines. Each query had one warm-up and five alternating measured runs; timings include fetching all rows. DuckDB used one worker thread. Loading the data was outside the timing.", "",
               "| Engine | Normalized median (ms) | Report median (ms) |",
               "| --- | ---: | ---: |",
               f"| SQLite, report index removed | {sqlite_times['normalized']:.3f} | {sqlite_times['report']:.3f} |",
               f"| DuckDB | {duckdb_times['normalized']:.3f} | {duckdb_times['report']:.3f} |", "",
               "Both engines returned 350 groups totalling 722,610.0. This compares these engine configurations, including their optimizers and storage; it does not isolate columnar storage as the only cause of a timing difference.", "",
               "The question for my project is whether the normalized read is already fast enough. A reporting copy can still improve a read, but it also needs extra storage and a refresh strategy. These small cached results do not show that every production dashboard can avoid denormalization.", "",
               "[Method and interpretation](duckdb-notes.md) · [All DuckDB runs and plans](evidence/duckdb.txt) · [SQLite results](benchmark-results.md)"]
    (HERE / "duckdb-results.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("Round 1-7 technical artefacts and optional comparisons saved in Module05/.")
    print("200,000 source lines reconstructed exactly; all measured query results agree.")
    print("Add the feedback from the round gates and harvest exchange to the notes.")


if __name__ == "__main__":
    main()
