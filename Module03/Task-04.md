# Task 4: One query, from algebra to plan

I used the city revenue dashboard query. Its job is to join customers, orders, order lines, and products; keep 2025 orders; group by city; count distinct customers; and sum line revenue.

## SQL

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

## Relational algebra

Let `R` be the joined rows:

```text
R = customer ⋈_(customer.customer_id = orders.customer_id) orders
    ⋈_(orders.order_id = order_line.order_id) order_line
    ⋈_(order_line.product_id = product.product_id) product
```

Then filter to 2025, project the columns using SQL bag semantics, and calculate the aggregates:

```text
γ_(city;
  COUNT(DISTINCT customer_id) → customers,
  SUM(qty × price) → revenue)
  (π_bag_(city, customer_id, qty, price)
    (σ_(ordered_on >= '2025-01-01' AND ordered_on < '2026-01-01')(R)))
```

`σ` is the `WHERE` filter, `π_bag` keeps the columns needed for the report and preserves duplicate rows, `⋈` matches related rows through their keys, and `γ` groups rows by city and calculates the aggregates. `ORDER BY revenue DESC` only sorts the final displayed rows; it does not change which rows or aggregate values the relational expression produces.

Two different order lines can have identical values in these four columns. A classical set projection would collapse them before `SUM` and change the revenue. An equivalent set-based expression can aggregate the full joined rows without that projection.

## Check

The expression has the same joins, year condition, grouping key, distinct customer count, and revenue calculation as the SQL. Running the SQL returned Bielefeld, Gütersloh, Münster, and Paderborn, each with 500 distinct customers, sorted by revenue descending.
