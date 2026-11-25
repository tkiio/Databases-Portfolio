"""Compare Snappy with Zstandard, using the same data and warm dashboard reads."""
import json
import statistics
import time
from pathlib import Path
import duckdb

HERE = Path(__file__).resolve().parent
source = HERE / "report_history.parquet"
target = HERE / "report_zstd.parquet"
literal = lambda path: "'" + str(path).replace("'", "''") + "'"
con = duckdb.connect()
con.execute(f"COPY (SELECT * FROM read_parquet({literal(source)})) TO {literal(target)} "
            "(FORMAT parquet, COMPRESSION zstd)")
query = """SELECT machine_id,site,technician,SUM(part_price) AS cost
FROM read_parquet(?) WHERE done_on >= '2026-01-01'
GROUP BY machine_id,site,technician"""
expected = sorted(con.execute(query, [str(source)]).fetchall())
assert sorted(con.execute(query, [str(target)]).fetchall()) == expected
times = {"snappy": [], "zstd": []}
paths = {"snappy": source, "zstd": target}
for repeat in range(5):
    order = ["snappy", "zstd"] if repeat % 2 == 0 else ["zstd", "snappy"]
    for name in order:
        start = time.perf_counter()
        rows = con.execute(query, [str(paths[name])]).fetchall()
        times[name].append((time.perf_counter()-start)*1000)
        assert sorted(rows) == expected
results = {}
for name,path in paths.items():
    count,total = con.execute("SELECT COUNT(*),SUM(part_price) FROM read_parquet(?)", [str(path)]).fetchone()
    codecs = con.execute("SELECT DISTINCT compression FROM parquet_metadata(?)", [str(path)]).fetchall()
    results[name] = {"bytes": path.stat().st_size, "runs_ms": times[name],
                     "median_ms": statistics.median(times[name]), "rows": count, "sum": total,
                     "codecs": [r[0] for r in codecs]}
    print(name, "bytes=",path.stat().st_size, "MB=",round(path.stat().st_size/1e6,3),
          "median_ms=",round(statistics.median(times[name]),3), "range_ms=",(min(times[name]),max(times[name])),
          "rows=",count,"sum=",total,"codecs=",codecs)
print("Five warm runs, alternating order; matching results. Export time excluded.")
(HERE/"evidence").mkdir(exist_ok=True)
(HERE/"evidence/compression.json").write_text(json.dumps(results,indent=2)+"\n")
con.close()
