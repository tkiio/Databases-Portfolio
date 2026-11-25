# Module06a/plan.py — run with:  uv run python Module06a/plan.py
"""The DuckDB physical plan: rows and time per operator (this runs the query)."""
import duckdb
import sqlite3
from pathlib import Path

here = Path(__file__).parent
pq = here / "report_history.parquet"

con = duckdb.connect()
plan = con.execute(f"""
    EXPLAIN ANALYZE
    SELECT machine_id, site, technician, SUM(part_price) AS cost
    FROM read_parquet('{pq}')
    WHERE done_on >= '2026-01-01'
    GROUP BY machine_id, site, technician
""").fetchall()[0][1]
print(plan)
print("\nSQLite plan for the same query:")
with sqlite3.connect((here / "history.db").resolve().as_uri() + "?mode=ro", uri=True) as sq:
    for row in sq.execute("""EXPLAIN QUERY PLAN
        SELECT machine_id, site, technician, SUM(part_price) AS cost
        FROM report_history WHERE done_on >= '2026-01-01'
        GROUP BY machine_id, site, technician"""):
        print(row[3])
con.close()
