# Task 5: Window functions and a subquery rewrite

The report counts each customer's late orders and sorts customers by that count. I compared the grouped query with a correlated-subquery version and a window-function version in `warehouse.db` (SQLite 3.54.0). Both rewrites returned the same 400 customers and late-order counts as the grouped query.

## Grouped reference query

```sql
SELECT c.customer_id, c.name, COUNT(*) AS late_orders
FROM orders o
JOIN customer c ON c.customer_id = o.customer_id
WHERE o.status = 'late'
GROUP BY c.customer_id, c.name
ORDER BY late_orders DESC;
```

## Correlated subquery

```sql
SELECT c.customer_id, c.name,
       (SELECT COUNT(*)
        FROM orders o
        WHERE o.customer_id = c.customer_id
          AND o.status = 'late') AS late_orders
FROM customer c
WHERE EXISTS (
    SELECT 1
    FROM orders o
    WHERE o.customer_id = c.customer_id
      AND o.status = 'late'
)
ORDER BY late_orders DESC;
```

`EXISTS` preserves the reference query's behavior: customers with zero late orders are excluded. The correlated count is readable as “for this customer, count matching late orders,” but the condition appears twice.

## Window-function rewrite

```sql
WITH late_by_customer AS (
    SELECT customer_id,
           COUNT(*) OVER (PARTITION BY customer_id) AS late_orders,
           ROW_NUMBER() OVER (
               PARTITION BY customer_id ORDER BY order_id
           ) AS rn
    FROM orders
    WHERE status = 'late'
)
SELECT c.customer_id, c.name, l.late_orders
FROM late_by_customer AS l
JOIN customer AS c ON c.customer_id = l.customer_id
WHERE l.rn = 1
ORDER BY l.late_orders DESC;
```

The window count is repeated on every late-order row for a customer, so `ROW_NUMBER()` and `rn = 1` keep one row per customer. This form is useful when the report also needs individual late-order rows, but it is more machinery for a count-only report.

## Plan comparison

The actual `EXPLAIN QUERY PLAN` output was:

Grouped reference:

```text
SCAN o
SEARCH c USING INTEGER PRIMARY KEY (rowid=?)
USE TEMP B-TREE FOR GROUP BY
USE TEMP B-TREE FOR ORDER BY
```

Correlated subquery:

```text
SCAN c
BLOOM FILTER ON o (customer_id=? AND status=?)
SEARCH o EXISTS USING AUTOMATIC PARTIAL COVERING INDEX (customer_id=? AND status=?)
CORRELATED SCALAR SUBQUERY 1
SCAN o
USE TEMP B-TREE FOR ORDER BY
```

Window function:

```text
CO-ROUTINE late_by_customer
  CO-ROUTINE (subquery-3)
    CO-ROUTINE (subquery-4)
      SCAN orders
      USE TEMP B-TREE FOR ORDER BY
    SCAN (subquery-4)
  SCAN (subquery-3)
SCAN l
SEARCH c USING INTEGER PRIMARY KEY (rowid=?)
USE TEMP B-TREE FOR ORDER BY
```

The grouped query scanned `orders`, looked up `customer` by integer primary key, and used temporary B-trees for grouping and ordering. The correlated form scanned customers, used an automatic partial covering index for its `EXISTS` check, then ran a correlated scalar subquery that scanned `orders`; it also used a temporary B-tree for ordering. The window form scanned late orders through co-routines, used temporary ordering for the window work, joined customers by primary key, and used a temporary B-tree for the final ordering.

These plans show why the grouped reference is the simplest fit for this aggregate-only report. The correlated version expresses the per-customer question directly but repeats the lookup; the window version keeps row-level detail available but requires deduplicating back to one row per customer. Plans and timing can change with indexes and database versions.

## LLM note

The two rewrites in this comparison were prepared with ChatGPT, GPT-6 Luna at medium thinking (the model setting identified for this chat). I checked them by running all three queries and comparing their full result sets; they matched. The grouped query was the reference/default form, while the correlated and window forms were the rewrites.
