# Module 3 — SQL notes

- In the dashboard, SQLite starts with `SCAN ol` and looks up the other tables by primary key. The order in the SQL is a way to describe the joins. SQLite can choose a different order for execution. [Dashboard plan](Task-01.md) · [SQLite query plan guide](https://sqlite.org/eqp.html)
- The date index changed the one-day lookup to `SEARCH o USING INDEX ix_orders_ordered_on`. Wrapping the date in `date()` brought back the scan, even with the index still in place. [Index benchmark](Task-02.md)
- A city with ten order lines for one customer still counts that customer once. The report needs `COUNT(DISTINCT customer_id)` for the customer count and every line for the revenue sum. [Algebra check](Task-04.md)

My question for the pod is how many runs we would want before saying a small timing difference really matters. I would start with the plan change and the spread of measured times.
