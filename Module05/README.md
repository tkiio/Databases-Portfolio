# Module 5 — Normalization and denormalization

In this module, my focus is on how the way tables are designed affects repeated data, updates, storage and query speed. My main question is whether making a dashboard faster is worth keeping another copy of its data.

## Learning goals

By the end of this module, you can:

1. Derive functional dependencies and identify candidate keys.
2. Normalize a relation to 1NF, 2NF and 3NF, explaining the anomaly each step removes.
3. Denormalize deliberately for a frequent read and predict the cost on writes and storage.
4. Measure query latency, write cost and database size before and after.
5. Defend a schema design based on the workload and measured results.

## My work by round

| Round | My files and evidence |
| --- | --- |
| 1 — See it | [FD list and ER sketches](fd-comparison.md), [side-by-side diagram](er-comparison.svg) |
| 2 — Break it | [Three anomalies](anomalies.sql), [experiment script](anomalies.py), [actual results](evidence/anomalies.txt) |
| 3 — Build it | [200,000-row setup](setup.sql), [3NF tables and loading](normalize.sql), [counts and reconstruction checks](evidence/build.txt) |
| 4 — Race it | [Report table](report.sql), [normalized query](dashboard-normalized.sql), [report query](dashboard-report.sql), [timings and plans](benchmark-results.md) |
| 5 — Price it | [Write and storage comparison](benchmark-results.md), [all runs](evidence/benchmark.txt) |
| 6 — Decide | [My recommendation to the operations lead](recommendation.md) |
| 7 — Harvest | [Curiosities and sources](curiosities.md) |
| Optional — more dimensions | [Wider schema](dimensions.sql), [measured results](benchmark-results.md#optional-wider-comparison) |
| Optional — DuckDB | [Comparison table](duckdb-results.md), [method](duckdb-notes.md), [script](duckdb_compare.py), [plans and output](evidence/duckdb.txt) |
| Reflection | [Reflection 5](../Reflections/ref05.md) |

The dataset is generated for this lab. My round-gate progress and the points still to discuss are in the notes.

## What I found difficult

Naming the FDs and deciding whether they were real rules or just patterns in the sample was difficult for me. Drawing the two ER sketches and comparing my reasoning with the model's answer was also challenging. The [FD page](fd-comparison.md) breaks that down using the five rows from the task.

## Rebuilding the lab

From the portfolio's top folder:

```sh
uv run python Module05/run_lab.py
```

The script creates the database and runs the anomalies, SQLite benchmarks, extra-dimension comparison and DuckDB comparison. The environment from earlier modules already includes DuckDB. If `normalize.db` exists, the script stops; to deliberately replace its generated lab data and refresh the evidence:

```sh
uv run python Module05/run_lab.py --reset
```

The smaller experiments can also be run separately:

```sh
uv run python Module05/anomalies.py
uv run python Module05/bench.py
uv run python Module05/duckdb_compare.py
```

The benchmark needs the tables created by the full lab. It temporarily changes one machine's site, restores it, and leaves the main reporting table without the machine index after comparing both states. A standalone rerun of `bench.py` refreshes the SQLite table and memo; a full run also refreshes the combined DuckDB comparison page.

To inspect the database:

```sh
sqlite3 Module05/normalize.db
```

Then use SQL and dot-commands at the SQLite prompt:

```sql
PRAGMA foreign_keys = ON;
.tables
.schema job_part
SELECT COUNT(*) FROM flat_jobpart;
SELECT COUNT(*) FROM part;
.quit
```

The source has 200,000 rows, 20,000 jobs, 50 machines and 10 parts. Both main dashboard queries return the same 350 groups and total cost of 722,610.0. The plans and each measured run are saved with the results.

## Files to commit

The SQL and Python scripts, notes, diagrams and evidence text/JSON files belong in the portfolio. `normalize.db` stays local and is excluded by `.gitignore`. The DuckDB comparison uses temporary files and removes them afterwards.

[Portfolio home](../README.md) · [Normalization notes](normalization-notes.md) · [Reflection 5](../Reflections/ref05.md)
