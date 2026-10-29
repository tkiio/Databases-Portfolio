# Task 2: Index benchmark

Database: `warehouse.db` (SQLite 3.54.0). The dashboard timings are from the same Mac and SQLite shell session with `.timer on`; each is the median of three runs. The single-day lookup timings use the same Python repeated-batch command before and after the index.

## LLM request and candidate indexes

Prompt used as the request template:

> Suggest indexes to test for this SQLite query. For each index, explain which filter or join it might help. Do not rewrite the query. I will test each index independently with `EXPLAIN QUERY PLAN` and repeated timings.

The candidates tested, as listed in the assignment, were:

```sql
CREATE INDEX ix_orders_ordered_on ON orders(ordered_on);
CREATE INDEX ix_orderline_order ON order_line(order_id);
CREATE INDEX ix_orderline_product ON order_line(product_id);
```

The exact model reply was not captured in my notes, so these are recorded as the assignment's candidates rather than quoted as the model's recommendations.

## Dashboard query and results

```sql
SELECT c.city, COUNT(DISTINCT c.customer_id) AS customers,
       SUM(ol.qty * p.price) AS revenue
FROM customer c
JOIN orders o ON o.customer_id = c.customer_id
JOIN order_line ol ON ol.order_id = o.order_id
JOIN product p ON p.product_id = ol.product_id
WHERE o.ordered_on >= '2025-01-01'
  AND o.ordered_on < '2026-01-01'
GROUP BY c.city
ORDER BY revenue DESC;
```

The query returned the same four city totals in each run: Bielefeld 500 / 11,242,176.0; Gütersloh 500 / 8,422,344.0; Münster 500 / 5,493,504.0; Paderborn 500 / 2,815,656.0.

| State (only the named candidate index was added) | Three real times (seconds) | Median | Dashboard plan |
| --- | --- | ---: | --- |
| No test index (baseline) | 0.073088, 0.072839, 0.073095 | 0.073088 s | `SCAN ol`; searches `o`, `c`, `p` by integer primary key; temporary B-trees for grouping, `COUNT(DISTINCT)`, and ordering |
| `ix_orders_ordered_on` | 0.087107, 0.069867, 0.071144 | 0.071144 s | Same plan; date index not used by dashboard |
| `ix_orderline_order` | 0.071483, 0.064827, 0.071240 | 0.071240 s | Same plan; still `SCAN ol` |
| `ix_orderline_product` | 0.069099, 0.049559, 0.063593 | 0.063593 s | Same plan; still `SCAN ol` |

The plans did not change for the dashboard. The median timings varied somewhat, but because the plan stayed the same, these runs do not establish that any candidate index reliably speeds up this aggregate-heavy query. The product index is not generally useless: it was used for a direct `WHERE product_id = 1` lookup (`SEARCH order_line USING INDEX ix_orderline_product`). It simply did not help this dashboard query.

## Single-day lookup: date index helps

Before adding `ix_orders_ordered_on`, the plan for this lookup was:

```text
SCAN o
SEARCH c USING INTEGER PRIMARY KEY (rowid=?)
```

After adding the index, the plan became:

```text
SEARCH o USING INDEX ix_orders_ordered_on (ordered_on=?)
SEARCH c USING INTEGER PRIMARY KEY (rowid=?)
```

The repeated-batch Python timing reported a median of **0.978 ms per lookup before** and **0.058 ms per lookup after** the index (about 17 times faster in this run).

## Negative result: function on indexed column

With the date index present, this query:

```sql
SELECT o.order_id, o.ordered_on, c.name
FROM orders o
JOIN customer c ON c.customer_id = o.customer_id
WHERE date(o.ordered_on) = '2026-02-14';
```

still produced:

```text
SCAN o
SEARCH c USING INTEGER PRIMARY KEY (rowid=?)
```

Wrapping the indexed column in `date()` changes the expression SQLite must evaluate, so the ordinary index on `ordered_on` is not used for this predicate. The plain equality predicate `o.ordered_on = '2026-02-14'` does use it.

## Conclusion

An index changes the access plan but does not guarantee a faster aggregate query. The date index made a clear difference for a selective single-day lookup, where the plan changed from a table scan to an indexed search. The same index did not change the dashboard plan, and applying a function to `ordered_on` defeated its use.
