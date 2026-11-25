# Module 6a — The Analytical Engine (DuckDB)

My focus in this module is choosing an engine based on the work it has to do. The race was the most interesting part for me, but the small-write test shows why a fast reporting engine is not automatically the best place for live updates.

## Learning goals

By the end of this module, you can:

1. Move a table from SQLite into Parquet reproducibly.
2. Compare the same aggregates in SQLite and DuckDB using interleaved runs and medians.
3. Read EXPLAIN ANALYZE and identify the main operator and row counts.
4. State, with a number, where DuckDB is the wrong engine.
5. Recommend what moves to an analytical copy and how it stays fresh.

## My portfolio evidence

| Work | Files and results |
| --- | --- |
| Build history | [prepare.py](prepare.py) — expands the Module 5 report to 2,000,000 rows |
| CSV to Parquet | [to_parquet.py](to_parquet.py), [matching counts, sums and sizes](evidence/sizes.txt) |
| Read benchmark | [race.py](race.py), [timing table](timings.md), [all runs](evidence/race.json) |
| Query plans | [plan.py](plan.py), [full plans](evidence/plans.txt), [marked operator in my notes](duckdb-notes.md#reading-the-plan) |
| Write/lookup boundary | [boundary.py](boundary.py), [numbers including executemany](evidence/boundary.txt) |
| Compression homework | [compare_compression.py](compare_compression.py), [Snappy/Zstandard results](evidence/compression.txt) |
| Recommendation | [Memo to Lea Winter and Yasmin Kaya](memo.md), including ownership, stale copies and failure detection |
| Refresh extension | [refresh.py](refresh.py), [two checked runs](evidence/refresh-check.txt), [failed-copy test](evidence/refresh-failure.txt) |
| Reflection | [Reflection 6a](../Reflections/ref06a.md) |

My [discussion notes](duckdb-notes.md#pod-discussion-notes) apply the race and refresh results to my maintenance and parts-cost project.

## Running the work

The existing history.db is reused. To refresh the copy, rerun the comparisons and update the saved notes:

```sh
uv run python Module06a/run_checks.py
```

This replaces the generated Parquet copies and evidence files. It reads history.db without changing it. The refresh uses a temporary CSV, so it needs some free disk space while running.

To check the current copy without rebuilding it:

```sh
uv run python Module06a/refresh.py --check-only
```

To rebuild and check before publishing:

```sh
uv run python Module06a/refresh.py --check
```

For a complete rebuild from Module 5, use prepare.py followed by to_parquet.py before the checks. prepare.py replaces history.db. Its CSV deliberately has 200,000 base rows; to_parquet.py expands them ten times.

The monthly query now uses `strftime('%Y-%m', done_on)` for both engines. The earlier reversed order returned NULL months in SQLite, so the corrected timings are the ones to use. The monthly COUNT(*) is labelled part_rows rather than jobs.

Commit the code, notes and small evidence files. Keep history.db, the generated CSV and the Parquet files local, with the large files ignored by Git.

[My notes](duckdb-notes.md) · [My timing table](timings.md) · [My memo](memo.md) · [Portfolio home](../README.md)
