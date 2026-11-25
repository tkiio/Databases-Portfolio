"""Update the timing table, notes and memo from the saved measurements."""
import json
import re
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "evidence"


def main():
    race = json.loads((OUT/"race.json").read_text())
    boundary = json.loads((OUT/"boundary.json").read_text())
    compression = json.loads((OUT/"compression.json").read_text())
    sizes = json.loads((OUT/"sizes.json").read_text())["bytes"]
    def median(mode,engine,op):
        return statistics.median(boundary[mode][engine][op])
    dashboard,monthly = race["dashboard"],race["monthly"]
    table = ["# My timing results", "",
             "Five warm runs per read query, with engine order alternated. Every result row is fetched inside the timer. Answers are compared before timing. Brackets give min–max, not a confidence interval.", "",
             "| Query | SQLite median [range], ms | DuckDB median [range], ms | Speedup |",
             "| --- | ---: | ---: | ---: |"]
    for name,item in race.items():
        a,b=item["sqlite_runs_ms"],item["duckdb_runs_ms"]
        table.append(f"| {name} | {item['sqlite_median_ms']:.2f} [{min(a):.2f}–{max(a):.2f}] | "
                     f"{item['duckdb_median_ms']:.2f} [{min(b):.2f}–{max(b):.2f}] | {item['speedup']:.1f}× |")
    table.extend(["",f"Dashboard: {dashboard['result_rows']} groups. Monthly: {monthly['result_rows']} groups. Each report totals 21,000,000.0.","",
        "The original monthly SQL had strftime arguments in the wrong order for SQLite, so its earlier timing was not a comparison of matching answers. The corrected query uses `strftime('%Y-%m', done_on)` in both engines. COUNT(*) is labelled part_rows because it counts job-part rows, not distinct jobs.","",
        "## Where DuckDB loses", "",
        "Each cell is the median of three runs of 1,000 operations, after a warm-up. Tables are fresh and in memory. These numbers include API overhead and do not measure disk durability.","",
        "| Insert method | SQLite inserts, ms | DuckDB inserts, ms | SQLite lookups, ms | DuckDB lookups, ms |",
        "| --- | ---: | ---: | ---: | ---: |"])
    for label,mode in [("Course single-row version","course_single"),("Single-row, one transaction each","single_transaction"),("executemany, one transaction each","executemany")]:
        table.append(f"| {label} | {median(mode,'sqlite','insert'):.3f} | {median(mode,'duckdb','insert'):.3f} | "
                     f"{median(mode,'sqlite','lookup'):.3f} | {median(mode,'duckdb','lookup'):.3f} |")
    improvement=median("single_transaction","duckdb","insert")/median("executemany","duckdb","insert")
    table.extend(["", "The course version gives SQLite one implicit write transaction but DuckDB autocommit. The second row controls that difference by giving both engines one explicit transaction. It still leaves a large gap here.", "",
                  f"With equal transaction scope, executemany improved DuckDB insert time by **{improvement:.2f}×** in this run. The result is measured rather than forced to match the handout's approximate 3×.","",
                  "## Files and compression", "", "| File | Bytes | MB (decimal) | Dashboard median, ms |", "| --- | ---: | ---: | ---: |",
                  f"| SQLite history.db | {sizes['history.db']:,} | {sizes['history.db']/1e6:.3f} | See read table |"])
    for name,file in [("snappy","report_history.parquet"),("zstd","report_zstd.parquet")]:
        item=compression[name]
        table.append(f"| {file} | {item['bytes']:,} | {item['bytes']/1e6:.3f} | {item['median_ms']:.3f} |")
    table.extend(["", "The compression comparison uses five warm alternating runs on the same query; row counts, sums and full dashboard answers match. It excludes export time. Different runs or exports can have different sizes and timings; the original course-generated file was about 2.32 MB, while this direct SQLite refresh can arrange/compress the same facts differently.","",
                  "[Read runs](evidence/race.txt) · [Write/lookup runs](evidence/boundary.txt) · [Compression runs](evidence/compression.txt) · [Memo](memo.md)"])
    (HERE/"timings.md").write_text("\n".join(table)+"\n")

    memo = [
        "I would keep current readings, corrections and small lookups in SQLite and move the reporting history into a Parquet copy for DuckDB.",
        f"The corrected dashboard fell from {dashboard['sqlite_median_ms']:.1f} ms in SQLite to {dashboard['duckdb_median_ms']:.1f} ms in DuckDB, and the monthly query fell from {monthly['sqlite_median_ms']:.1f} ms to {monthly['duckdb_median_ms']:.1f} ms.",
        f"The SQLite file is {sizes['history.db']/1e6:.2f} MB, while the refreshed Snappy copy is {compression['snappy']['bytes']/1e6:.2f} MB and the Zstandard copy is {compression['zstd']['bytes']/1e6:.2f} MB.",
        f"I would not move repeated single-row requests: with one transaction in each engine, 1,000 inserts took {median('single_transaction','sqlite','insert'):.2f} ms in SQLite and {median('single_transaction','duckdb','insert'):.2f} ms in DuckDB.",
        "I would schedule refresh.py --check at 01:30 before the 02:00 report, with the shift lead responsible for checking whether the scheduled job succeeded.",
        "The refresh builds a temporary copy, checks it and then replaces the visible Parquet file so readers get a complete file.",
        "If the copy is a day old, it may miss new jobs and corrections, so I would show its age, alert on refresh failure and withhold a current-day report until a valid refresh is available.",
        "For this workload I would rather show an older report clearly labelled than silently present stale numbers as current, and I would rerun the refresh or use the slower SQLite query when current data is required.",
    ]
    extra = ("The compression result is a smaller file with similar warm query time; it is not a promise that Zstandard always makes reads faster. "
             "The scheduler would capture the refresh exit status and log, while a separate check would alert if the Parquet file's modification time is too old even when the scheduler stops running. "
             "The --check option compares row count and SUM(part_price) to one SQLite snapshot, which catches incomplete copies and many wrong-source mistakes, but it cannot prove that every column matches, detect offsetting price errors, or guarantee that the source itself is fresh. "
             "New SQLite writes after that snapshot will wait for the next refresh.")
    (HERE/"memo.md").write_text("# Memo to Lea Winter and Yasmin Kaya\n\n"+" ".join(memo)+"\n\n"+extra+
        "\n\n[My timing table](timings.md) · [Two checked refreshes](evidence/refresh-check.txt)\n")

    plan=(OUT/"plans.txt").read_text()
    operators={}
    for name in ("HASH_GROUP_BY","PROJECTION","TABLE_SCAN"):
        if name in plan:
            block=plan.split(name,1)[1].split("└",1)[0]
            values=re.findall(r"([0-9]+\.[0-9]+)s",block)
            if values:operators[name]=float(values[-1])
    dominant=max(operators,key=operators.get) if operators else "HASH_GROUP_BY (inspect raw plan)"
    notes = f"""# Module 6a — My DuckDB notes

The race was the most interesting part of this module for me. The useful question is which kind of work each engine handles well.

## Export and checks

prepare.py creates 2,000,000 SQLite history rows and exports a 200,000-row base CSV. to_parquet.py repeats that base ten times, so it should not be given an already expanded two-million-row CSV. Both final sides contain 2,000,000 rows and SUM(part_price) = 21,000,000.0. [Counts and sizes](evidence/sizes.txt)

## Reading the plan

**Marked operator: {dominant}**, with reported cumulative time {operators.get(dominant,0):.2f}s in this profile. [Full EXPLAIN ANALYZE and SQLite plan](evidence/plans.txt)

DuckDB's scan reads 2,000,000 rows from the required columns. The projection passes them to grouping, which produces 350 machine/site/technician groups. SQLite shows SCAN report_history and USE TEMP B-TREE FOR GROUP BY. The operator times can overlap across parallel threads, so they should not be added together as elapsed time. The broad date condition includes the whole fixture; this plan does not prove that date row groups were skipped.

## Checking the race

The initial monthly statement used strftime(done_on, '%Y-%m'). That order works in DuckDB but returns NULL months in SQLite, which expects the format first. Comparing answers caught this. race.py now uses the format-first version in both engines and checks all result values before timing. COUNT(*) counts part rows, so the alias is part_rows. [Corrected timings](timings.md)

The read measurements use a warm-up and five runs with alternating engine order. They include fetching the results and exclude loading/export time. They are results on this laptop and dataset, not a universal speed guarantee.

## Where I would keep SQLite

For Kortmann, DuckDB is the wrong engine for lots of separate single-reading inserts and indexed point lookups. In the equal-transaction test, 1,000 lookups took {median('single_transaction','sqlite','lookup'):.3f} ms in SQLite and {median('single_transaction','duckdb','lookup'):.3f} ms in DuckDB. [Full insert/lookup evidence](evidence/boundary.txt)

Each INSERT needs its parameters bound, a statement processed, constraints/indexes maintained and transaction work handled. A scan can process many rows through the same operators. The course code also has different transaction scope, so the extra test gives both engines one transaction. These databases are in memory, so this is not measuring disk fsync cost.

executemany improved the measured insert time but did not close the gap. It repeats a parameterized statement rather than turning the input into a columnar bulk scan. The application would need to collect rows into larger batches and load them through COPY or a similar bulk path, accepting the delay before a batch is available. A real-time alarm or immediate correction may not be able to wait.

For my maintenance project, I would record a job and the parts used in one SQLite transaction. The supervisor needs to see a new repair right away in the 90-day view. If the workshop later needs to group years of parts costs by machine, I would export a reporting copy and use DuckDB for that history.

## Compression extension

I chose the Snappy/Zstandard comparison. The Zstandard file is smaller in this run and its warm dashboard time is similar. The [compression output](evidence/compression.txt) records sizes, codecs, times and matching totals. This does not show that a smaller file always makes a cached query faster. The JSON and sorted-row-group extensions were not attempted.

## Refresh pipeline

refresh.py rebuilds from history.db using a temporary local CSV and DuckDB COPY. No extension download is needed. SQLite counts and exported rows share a read transaction. With --check, a failed count/sum comparison stops publication and returns 1. The final file is replaced atomically on the same filesystem.

Two runs of `uv run python Module06a/refresh.py --check` are recorded below. Each keeps the same row count and sum; this is idempotence of those logical checks, not a promise of identical bytes or a proof of every row's contents.

```text
{(OUT/'refresh-check.txt').read_text().strip()}
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
"""
    (HERE/"duckdb-notes.md").write_text(notes)


if __name__ == "__main__":
    main()
