# Module 6a — My DuckDB notes

The race was the most interesting part of this module for me. The useful question is which kind of work each engine handles well.

## Export and checks

prepare.py creates 2,000,000 SQLite history rows and exports a 200,000-row base CSV. to_parquet.py repeats that base ten times, so it should not be given an already expanded two-million-row CSV. Both final sides contain 2,000,000 rows and SUM(part_price) = 21,000,000.0. [Counts and sizes](evidence/sizes.txt)

## Reading the plan

**Marked operator: HASH_GROUP_BY**, with reported cumulative time 0.03s in this profile. [Full EXPLAIN ANALYZE and SQLite plan](evidence/plans.txt)

DuckDB's scan reads 2,000,000 rows from the required columns. The projection passes them to grouping, which produces 350 machine/site/technician groups. SQLite shows SCAN report_history and USE TEMP B-TREE FOR GROUP BY. The operator times can overlap across parallel threads, so they should not be added together as elapsed time. The broad date condition includes the whole fixture; this plan does not prove that date row groups were skipped.

## Checking the race

The initial monthly statement used strftime(done_on, '%Y-%m'). That order works in DuckDB but returns NULL months in SQLite, which expects the format first. Comparing answers caught this. race.py now uses the format-first version in both engines and checks all result values before timing. COUNT(*) counts part rows, so the alias is part_rows. [Corrected timings](timings.md)

The read measurements use a warm-up and five runs with alternating engine order. They include fetching the results and exclude loading/export time. They are results on this laptop and dataset, not a universal speed guarantee.

## Where I would keep SQLite

For Kortmann, DuckDB is the wrong engine for lots of separate single-reading inserts and indexed point lookups. In the equal-transaction test, 1,000 lookups took 0.457 ms in SQLite and 100.495 ms in DuckDB. [Full insert/lookup evidence](evidence/boundary.txt)

Each INSERT needs its parameters bound, a statement processed, constraints/indexes maintained and transaction work handled. A scan can process many rows through the same operators. The course code also has different transaction scope, so the extra test gives both engines one transaction. These databases are in memory, so this is not measuring disk fsync cost.

executemany improved the measured insert time but did not close the gap. It repeats a parameterized statement rather than turning the input into a columnar bulk scan. The application would need to collect rows into larger batches and load them through COPY or a similar bulk path, accepting the delay before a batch is available. A real-time alarm or immediate correction may not be able to wait.

For my maintenance project, I would record a job and the parts used in one SQLite transaction. The supervisor needs to see a new repair right away in the 90-day view. If the workshop later needs to group years of parts costs by machine, I would export a reporting copy and use DuckDB for that history.

## Compression extension

I chose the Snappy/Zstandard comparison. The Zstandard file is smaller in this run and its warm dashboard time is similar. The [compression output](evidence/compression.txt) records sizes, codecs, times and matching totals. This does not show that a smaller file always makes a cached query faster. The JSON and sorted-row-group extensions were not attempted.

## Refresh pipeline

refresh.py rebuilds from history.db using a temporary local CSV and DuckDB COPY. No extension download is needed. SQLite counts and exported rows share a read transaction. With --check, a failed count/sum comparison stops publication and returns 1. The final file is replaced atomically on the same filesystem.

Two runs of `uv run python Module06a/refresh.py --check` are recorded below. Each keeps the same row count and sum; this is idempotence of those logical checks, not a promise of identical bytes or a proof of every row's contents.

```text
Run 1: uv run python Module06a/refresh.py --check
SQLite rows=2000000 sum=21000000.00
Parquet rows=2000000 sum=21000000.00
check: PASS
rows=2000000 checksum_sum=21000000.00 parquet_bytes=2464491 elapsed_ms=1965.8

Run 2: uv run python Module06a/refresh.py --check
SQLite rows=2000000 sum=21000000.00
Parquet rows=2000000 sum=21000000.00
check: PASS
rows=2000000 checksum_sum=21000000.00 parquet_bytes=2464491 elapsed_ms=1949.2
```

A deliberately wrong one-row Parquet file was also rejected with exit status 1. [Failure test](evidence/refresh-failure.txt) The --check-only option checks the current copy without overwriting it. Count and sum can miss changes to site/technician or offsetting price errors, so the memo also needs freshness and failure monitoring.

## Pod discussion notes

I would show the race first and then ask when a one-day-old copy would be good enough. For comparing last month's costs, I could use a dated snapshot. For deciding which machine to inspect today, I would check the current SQLite data. The [memo](memo.md) explains who owns the refresh and how to spot a failed one.

## Sources

- [DuckDB profiling](https://duckdb.org/docs/1.5/guides/meta/explain_analyze): operator rows and cumulative timings.
- [DuckDB insertion](https://duckdb.org/docs/1.5/data/insert): per-statement overhead and transactions.
- [Python DB API](https://duckdb.org/docs/1.5/clients/python/dbapi): executemany is not the recommended bulk-loading path.
- [Parquet files](https://duckdb.org/docs/1.5/data/parquet/overview): compression, projections and COPY.
- [SQLite date functions](https://sqlite.org/lang_datefunc.html): strftime(format, time-value).
- [SQLite query plans](https://sqlite.org/eqp.html): SCAN and temporary B-trees.

[Module overview](README.md) · [Timing table](timings.md) · [Memo](memo.md)
