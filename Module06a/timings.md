# My timing results

Five warm runs per read query, with engine order alternated. Every result row is fetched inside the timer. Answers are compared before timing. Brackets give min–max, not a confidence interval.

| Query | SQLite median [range], ms | DuckDB median [range], ms | Speedup |
| --- | ---: | ---: | ---: |
| dashboard | 696.48 [693.91–700.59] | 5.63 [5.39–5.74] | 123.7× |
| monthly | 811.93 [807.66–813.55] | 4.53 [4.33–4.82] | 179.2× |

Dashboard: 350 groups. Monthly: 1500 groups. Each report totals 21,000,000.0.

The original monthly SQL had strftime arguments in the wrong order for SQLite, so its earlier timing was not a comparison of matching answers. The corrected query uses `strftime('%Y-%m', done_on)` in both engines. COUNT(*) is labelled part_rows because it counts job-part rows, not distinct jobs.

## Where DuckDB loses

Each cell is the median of three runs of 1,000 operations, after a warm-up. Tables are fresh and in memory. These numbers include API overhead and do not measure disk durability.

| Insert method | SQLite inserts, ms | DuckDB inserts, ms | SQLite lookups, ms | DuckDB lookups, ms |
| --- | ---: | ---: | ---: | ---: |
| Course single-row version | 0.368 | 241.275 | 0.459 | 100.884 |
| Single-row, one transaction each | 0.366 | 198.408 | 0.457 | 100.495 |
| executemany, one transaction each | 0.212 | 173.946 | 0.458 | 101.871 |

The course version gives SQLite one implicit write transaction but DuckDB autocommit. The second row controls that difference by giving both engines one explicit transaction. It still leaves a large gap here.

With equal transaction scope, executemany improved DuckDB insert time by **1.14×** in this run. The result is measured rather than forced to match the handout's approximate 3×.

## Files and compression

| File | Bytes | MB (decimal) | Dashboard median, ms |
| --- | ---: | ---: | ---: |
| SQLite history.db | 112,685,056 | 112.685 | See read table |
| report_history.parquet | 2,464,491 | 2.464 | 5.513 |
| report_zstd.parquet | 1,442,397 | 1.442 | 5.586 |

The compression comparison uses five warm alternating runs on the same query; row counts, sums and full dashboard answers match. It excludes export time. Different runs or exports can have different sizes and timings; the original course-generated file was about 2.32 MB, while this direct SQLite refresh can arrange/compress the same facts differently.

[Read runs](evidence/race.txt) · [Write/lookup runs](evidence/boundary.txt) · [Compression runs](evidence/compression.txt) · [Memo](memo.md)
