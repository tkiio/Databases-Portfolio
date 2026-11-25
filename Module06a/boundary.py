"""Compare 1,000 single inserts/lookups and executemany; three measured runs."""
import json
import sqlite3
import statistics
import time
from pathlib import Path
import duckdb

N = 1000
RUNS = 3
rows = [(i, f"k{i}", i * 1.5) for i in range(N)]


def run(engine, mode):
    con = sqlite3.connect(":memory:") if engine == "sqlite" else duckdb.connect()
    try:
        con.execute("CREATE TABLE s(id INTEGER PRIMARY KEY,k TEXT,v DOUBLE)")
        # Course case: SQLite batches the transaction implicitly; DuckDB uses
        # autocommit. The two other cases use one transaction in BOTH engines.
        if mode != "course_single":
            con.execute("BEGIN TRANSACTION")
        start = time.perf_counter()
        if mode == "executemany":
            con.executemany("INSERT INTO s VALUES (?, ?, ?)", rows)
        else:
            for row in rows:
                con.execute("INSERT INTO s VALUES (?, ?, ?)", row)
        con.commit()
        insert = (time.perf_counter()-start)*1000
        assert con.execute("SELECT COUNT(*),SUM(v) FROM s").fetchone() == (N, 749250.0)
        start = time.perf_counter()
        answers = [con.execute("SELECT v FROM s WHERE id=?", (i,)).fetchone()[0] for i in range(N)]
        lookup = (time.perf_counter()-start)*1000
        assert answers == [row[2] for row in rows]
        return insert, lookup
    finally:
        con.close()


results = {}
for mode in ("course_single", "single_transaction", "executemany"):
    times = {engine: {"insert": [], "lookup": []} for engine in ("sqlite", "duckdb")}
    for engine in times:
        run(engine, mode)  # untimed warm-up
    for repeat in range(RUNS):
        for engine in (["sqlite", "duckdb"] if repeat % 2 == 0 else ["duckdb", "sqlite"]):
            insert,lookup = run(engine,mode)
            times[engine]["insert"].append(insert)
            times[engine]["lookup"].append(lookup)
    results[mode] = times
    print("\n",mode)
    for engine, cases in times.items():
        for operation, values in cases.items():
            print(engine,operation,"median_ms=",round(statistics.median(values),3),
                  "runs_ms=",[round(v,3) for v in values])
print("\nN=1000 per run; three measured runs plus a warm-up; fresh in-memory tables.")
print("course_single reproduces the course transaction difference; compare single_transaction for equal transaction scope.")
print("executemany also uses one transaction per engine. It is not a columnar bulk COPY.")
print("These are in-memory API timings, not disk durability measurements.")
print("Versions:",sqlite3.sqlite_version,duckdb.__version__)
here=Path(__file__).resolve().parent
(here/"evidence").mkdir(exist_ok=True)
(here/"evidence/boundary.json").write_text(json.dumps(results,indent=2)+"\n")
