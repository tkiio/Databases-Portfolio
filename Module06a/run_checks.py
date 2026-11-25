"""Run the remaining Module 6a experiments and capture their output.

Requires the existing history.db. Refreshes the analytical copy, not SQLite.
"""
import json
import sqlite3
import subprocess
import sys
import platform
from datetime import datetime, timezone
import tempfile
from pathlib import Path
import duckdb

HERE = Path(__file__).resolve().parent
OUT = HERE / "evidence"
OUT.mkdir(exist_ok=True)
(OUT/"run-info.txt").write_text(f"UTC: {datetime.now(timezone.utc).isoformat()}\n"
                              f"Python: {sys.version.split()[0]} SQLite: {sqlite3.sqlite_version} "
                              f"DuckDB: {duckdb.__version__}\nPlatform: {platform.system()} {platform.machine()}\n")


def run(script, args=(), expected=0):
    proc = subprocess.run([sys.executable,str(HERE/script),*args],
                          capture_output=True,text=True,timeout=240)
    if proc.returncode != expected:
        raise RuntimeError(proc.stdout + proc.stderr)
    return proc.stdout + proc.stderr


refresh = []
for repeat in (1,2):
    refresh.append(f"Run {repeat}: uv run python Module06a/refresh.py --check\n" + run("refresh.py",["--check"]))
(OUT/"refresh-check.txt").write_text("\n".join(refresh))
print("Two refresh/check runs passed.",flush=True)
(OUT/"refresh-existing.txt").write_text(run("refresh.py",["--check-only"]))
with tempfile.TemporaryDirectory(prefix="refresh-mismatch-") as folder:
    bad = Path(folder)/"wrong.parquet"
    con = duckdb.connect()
    quoted = str(bad).replace("'","''")
    con.execute(f"COPY (SELECT 1.0 AS part_price) TO '{quoted}' (FORMAT parquet)")
    con.close()
    failure = run("refresh.py",["--check-only","--parquet",str(bad)],expected=1)
    (OUT/"refresh-failure.txt").write_text("Controlled test: a temporary one-row copy, not the real report.\n"+failure+"Exit status: 1\n")

for script,target in [("race.py","race.txt"),("plan.py","plans.txt"),
                      ("boundary.py","boundary.txt"),("compare_compression.py","compression.txt")]:
    (OUT/target).write_text(run(script))
    print("Saved",target,flush=True)

with sqlite3.connect((HERE/"history.db").resolve().as_uri()+"?mode=ro",uri=True) as sq:
    sqlite_totals = sq.execute("SELECT COUNT(*),SUM(part_price) FROM report_history").fetchone()
    assert sq.execute("PRAGMA integrity_check").fetchone() == ("ok",)
con = duckdb.connect()
parquet_totals = con.execute("SELECT COUNT(*),SUM(part_price) FROM read_parquet(?)",[str(HERE/"report_history.parquet")]).fetchone()
assert sqlite_totals == parquet_totals == (2000000,21000000.0)
con.close()
sizes = {name:(HERE/name).stat().st_size for name in ("history.db","report_history.parquet","report_zstd.parquet")}
(OUT/"sizes.json").write_text(json.dumps({"bytes":sizes,"sqlite_totals":sqlite_totals,
                                           "parquet_totals":parquet_totals},indent=2)+"\n")
(OUT/"sizes.txt").write_text("\n".join(f"{name}: {size} bytes ({size/1e6:.3f} MB)" for name,size in sizes.items())+
                             f"\nSQLite: {sqlite_totals}\nParquet: {parquet_totals}\n")
print("Counts, price sums and database integrity checked.")
subprocess.run([sys.executable,str(HERE/"write_notes.py")],check=True)
