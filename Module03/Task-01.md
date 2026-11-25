# Task 1 — City dashboard and query plan

## Assignment prompt

> SQLite schema: `customer(customer_id, name, city)`, `product(product_id, sku, price)`, `orders(order_id, customer_id, ordered_on, status)`, `order_line(order_id, product_id, qty)`. Write a query that returns, for each city, the number of distinct customers and the total revenue (sum of `qty*price`) of orders placed in 2025, ordered by revenue descending.

## Reference query tested

```sql
SELECT c.city, COUNT(DISTINCT c.customer_id) AS customers,
       SUM(ol.qty * p.price) AS revenue
FROM customer c
JOIN orders o      ON o.customer_id = c.customer_id
JOIN order_line ol ON ol.order_id = o.order_id
JOIN product p     ON p.product_id = ol.product_id
WHERE o.ordered_on >= '2025-01-01'
  AND o.ordered_on <  '2026-01-01'
GROUP BY c.city
ORDER BY revenue DESC;
```

## My predicted plan

I expected SQLite to scan orders to find rows from 2025. For each matching order, I expected it to search customer by customer_id, order_line by order_id, and product by product_id. I expected temporary work for grouping by city, counting distinct customers, and sorting by revenue from the product.

## Actual plan

```text
QUERY PLAN
|--SCAN ol
|--SEARCH o USING INTEGER PRIMARY KEY (rowid=?)
|--SEARCH c USING INTEGER PRIMARY KEY (rowid=?)
|--SEARCH p USING INTEGER PRIMARY KEY (rowid=?)
|--USE TEMP B-TREE FOR GROUP BY
|--USE TEMP B-TREE FOR count(DISTINCT)
`--USE TEMP B-TREE FOR ORDER BY
```

The main difference was that SQLite started with a full scan of `order_line` and looked up each order by primary key. The grouping, distinct count and sort used temporary B-trees.

## Correctness check

The date range includes all of 2025. The query counts each customer only once per city, even when they have several order lines. Because the joins are inner joins, it counts customers with qualifying order lines. A separate check against the local fixture found 500 qualifying customers and zero customers without qualifying lines in each of the four cities. If the report was meant to count every customer, including customers without any 2025 purchases, it would need to start with all customers and keep those unmatched rows.
