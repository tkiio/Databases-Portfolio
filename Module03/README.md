# Module 3 — SQL, query plans and indexes

This module uses a small warehouse database to check what a SQL query returns and how SQLite runs it.

| Task | Evidence | What I learned |
| --- | --- | --- |
| 1 | [City dashboard and query plan](Task-01.md) | SQLite can start with a different table than I predicted. |
| 2 | [Index benchmark](Task-02.md) | The date index helped a single-day lookup. The dashboard still used its original plan. |
| 3 | [Bound parameters](Task-03.md) | SQL values should be passed separately from the query text. |
| 4 | [Relational algebra](Task-04.md) | Filtering, joining, projecting and grouping each do a different job. |
| 5 | [Optional query rewrites](Task-05.md) | The grouped, correlated and window queries returned the same counts. |

[Study notes and questions](sql-notes.md) · [Reflection 3](../Reflections/ref03.md) · [Portfolio home](../README.md)

[The setup script](setup.sql) builds the local warehouse database. From the portfolio root, run `sqlite3 Module03/warehouse.db < Module03/setup.sql` to create it. The database file stays local.
