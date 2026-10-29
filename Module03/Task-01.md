# LLM prompt

Use the reference query in step 2 as though the model had produced it, and critique it: is the year filter in the right place? Is the customer count really distinct? Does the query still answer the question when a customer has no orders? The verification work — which is the actual skill — is identical, and a podmate's model output works just as well.
# LLM'S sql

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

# Predicted Query Plan
Prediction: I expect SQLite to scan orders to find rows from 2025. For each matching order, I expect it to search customer by customer_id, order_line by order_id, and product by product_id. I expect temporary work for grouping by city, counting distinct customers, and sorting by revenue.

# Actual Query PLan
QUERY PLAN
|--SCAN ol
|--SEARCH o USING INTEGER PRIMARY KEY (rowid=?)
|--SEARCH c USING INTEGER PRIMARY KEY (rowid=?)
|--SEARCH p USING INTEGER PRIMARY KEY (rowid=?)
|--USE TEMP B-TREE FOR GROUP BY
|--USE TEMP B-TREE FOR count(DISTINCT)
`--USE TEMP B-TREE FOR ORDER BY

# CORRECTNESS NOTE 

The query ran and returned one row per city, counting distinct customers and summing quantity × product price for 2025 orders. The plan scans order_line, searches orders, customer, and product by their primary keys, and uses temporary B-trees for grouping, distinct counting, and sorting. Each city shows 500 customers; I should check whether that matches the data rather than assume it is correct.