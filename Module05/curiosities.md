# My Module 5 harvest

These are the points I want to bring to the pod's list swap. The exchange and any unanswered question for `#sql-questions` are still to record.

| What caught my attention | What to check or discuss | Source |
| --- | --- | --- |
| `CROSS JOIN` makes the dataset much larger | 20,000 jobs paired with ten part rows creates 200,000 combinations. | [SQLite SELECT and joins](https://sqlite.org/lang_select.html) |
| `% 40` does not mean forty generated parts | There are only ten input values for k. Count distinct results instead of guessing from the formula. | [My setup](setup.sql), [actual counts](evidence/build.txt) |
| Five rows can suggest a false FD | One technician per machine happens in the sample, but the bulk data has several. What is a rule, and what is an accident? | [My FD comparison](fd-comparison.md) |
| `printf('%.2f', ...)` produces text | Formatting a number is different from choosing a numeric storage type. | [SQLite printf](https://sqlite.org/printf.html), [data types](https://sqlite.org/datatype3.html) |
| REAL is not exact decimal money | The generated whole-number prices sum exactly here, but that does not make every decimal price exact. Integer minor units can avoid that issue. | [SQLite floating point](https://sqlite.org/floatingpoint.html) |
| DISTINCT is not an inconsistency repair | Conflicting job details can still give two distinct rows with the same job key and make the load fail. | [SQLite SELECT](https://sqlite.org/lang_select.html), [primary-key constraints](https://sqlite.org/lang_createtable.html) |
| SCAN USING INDEX can be slower | Following an entire index and fetching table rows can cost more than reading the table sequentially. | [SQLite query plans](https://sqlite.org/eqp.html), [my measurements](benchmark-results.md) |
| Table storage is not the whole design's storage | The handout's named-table dbstat query excludes their index pages. | [SQLite dbstat](https://sqlite.org/dbstat.html) |
| Two sessions do not bypass a duplicated fact | SQLite serializes writers, but partial edits can still leave inconsistent copies after both commits. | [SQLite isolation](https://sqlite.org/isolation.html), [my anomaly output](evidence/anomalies.txt) |
| A reporting copy needs a freshness rule | Changing the source does not automatically change a copied table. A refresh can also fail. | [My memo](recommendation.md), [SQLite transactions](https://sqlite.org/lang_transaction.html) |
| A star schema is not one completely flat table | A fact table normally stores measures and dimension keys; dimensions keep descriptive attributes. | [Microsoft star-schema guidance](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema) |
| DuckDB changes more than one thing | The engine has its own storage, optimizer and execution strategy; the measured difference does not isolate only column layout. | [DuckDB execution](https://duckdb.org/internals/vector), [my comparison](duckdb-results.md) |

My question for the group is: if the normalized query is already fast enough for the dashboard, is the smaller read time worth another copy to maintain?

[Module 5](README.md) · [My notes](normalization-notes.md)
