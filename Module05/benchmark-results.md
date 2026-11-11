# My benchmark results

Wall-clock medians from five warm runs per query, on one Python SQLite connection. All result rows were fetched and compared. These are measured laptop results, not the production story's 40 seconds.

| Design | Dashboard median (ms) | Site-update median (ms) | Rows updated | Table storage (KiB) | Tables + indexes (KiB) | Redundancy |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Normalized (3NF) | 28.130 | 0.234 | 1 | 3976.0 | 7976.0 | Facts stored once in their own tables |
| Report, with machine index | 27.064 | 8.851 | 4,000 | 10832.0 | 13752.0 | Site, technician and price repeated |
| Report, without machine index | 19.804 | Not measured | 4,000 | 10832.0 | 10832.0 | Same repeated facts |

The site updates were measured with the report index present. No separate no-index write timing is claimed.

The paired no-index rerun measured the normalized query again at **27.296 ms**. Compare both timings within the same paired experiment. The normalized time also changed between phases, so the entire report-time difference cannot be assigned to the index alone.

Table-only storage matches the handout's dbstat query. The additional column counts associated indexes, including primary-key indexes. The flat source and optional wider report are excluded from these design totals. Keeping a report alongside 3NF adds its storage; it does not replace the source tables.

The dataset has 200,000 lines, 20,000 jobs, 50 machines and 10 parts. Both main queries return 350 groups and a total of 722,610.0. The WHERE clause is a fixed lower date bound, not a rolling 90-day window.

## Optional wider comparison

The wider test uses six normalized tables (five joins) and a separate reporting copy with no machine index, so it leaves the main experiment intact.

Normalized median: **48.007 ms**. Report median: **33.901 ms**. Both return 3,500 groups totalling 722,610.0.

[All runs, plans and storage](evidence/benchmark.txt) · [Machine-readable measurements](evidence/benchmark.json) · [My recommendation](recommendation.md)
