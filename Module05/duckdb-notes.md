# Optional comparison — DuckDB

The question here is whether changing the engine reduces the benefit of the separate reporting table. The [comparison script](duckdb_compare.py) copies the same SQLite tables into a temporary DuckDB database and runs both dashboard queries. The [saved output](evidence/duckdb.txt) is the place to check the actual plans, times and result checks.

The copy happens before timing. The script uses local CSV files and DuckDB's bulk COPY command, so it does not download a SQLite extension. It warms both queries once, alternates their order over five measured runs, fetches every result row, and reports the medians. It also checks every answer against the source SQLite result, rather than comparing only the number of rows.

The date remains ISO-formatted text in both versions, and site is explicitly included in GROUP BY for SQL that both engines accept. DuckDB runs with one worker thread in this experiment, so a difference is not just the result of allowing it more threads than SQLite. Primary keys are declared, but no extra dashboard indexes are added.

The result I want to compare is the read-time benefit of the reporting table in each engine. A smaller benefit in DuckDB would support keeping the normalized source for this particular workload. A faster report would still need a refresh strategy, and neither result proves that every production dashboard can avoid denormalization.

Sources: [DuckDB CSV loading](https://duckdb.org/docs/stable/data/csv/overview), [DuckDB EXPLAIN](https://duckdb.org/docs/stable/guides/meta/explain).

The [comparison table](duckdb-results.md) brings the measured SQLite and DuckDB results together.
