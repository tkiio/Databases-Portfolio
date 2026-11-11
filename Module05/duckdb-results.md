# My DuckDB comparison

The same data and answers were checked in both engines. Each query had one warm-up and five alternating measured runs; timings include fetching all rows. DuckDB used one worker thread. Loading the data was outside the timing.

| Engine | Normalized median (ms) | Report median (ms) |
| --- | ---: | ---: |
| SQLite, report index removed | 27.296 | 19.804 |
| DuckDB | 2.720 | 1.580 |

Both engines returned 350 groups totalling 722,610.0. This compares these engine configurations, including their optimizers and storage; it does not isolate columnar storage as the only cause of a timing difference.

The question for my project is whether the normalized read is already fast enough. A reporting copy can still improve a read, but it also needs extra storage and a refresh strategy. These small cached results do not show that every production dashboard can avoid denormalization.

[Method and interpretation](duckdb-notes.md) · [All DuckDB runs and plans](evidence/duckdb.txt) · [SQLite results](benchmark-results.md)
