# Task 7 — LLM SQL verification

## Prompt

Here is my SQLite table: readings(ts TEXT, machine TEXT, temp_c REAL, vib_rms REAL, spindle_load REAL). Write a query that returns, for each machine, the average spindle load for readings taken overnight (after 18:00), ordered by average load descending.

## Generated SQL

    SELECT machine, AVG(spindle_load) AS avg_spindle_load
    FROM readings
    WHERE time(ts) > '18:00:00'
    GROUP BY machine
    ORDER BY avg_spindle_load DESC;

## Run result

The query ran successfully. Results, ordered by average spindle load:

| Machine | Average spindle load |
| --- | ---: |
| cnc-03 | 60.434 |
| cnc-01 | 60.368 |
| cnc-02 | 60.357 |

Runtime: 0.033322 seconds.

## Query plan

    QUERY PLAN
    |--SCAN readings
    |--USE TEMP B-TREE FOR GROUP BY
    `--USE TEMP B-TREE FOR ORDER BY

SQLite scans the readings table to evaluate the query. It also uses temporary B-trees for grouping and ordering.

## Break-it comparison

I tried the risky filter WHERE ts LIKE '%18%'. It returned different averages:

| Machine | Average spindle load |
| --- | ---: |
| cnc-03 | 61.123 |
| cnc-02 | 61.018 |
| cnc-01 | 60.996 |

This changed the order of the machines: cnc-02 moved ahead of cnc-01. The LIKE pattern finds 18 anywhere in the timestamp, rather than checking whether the time is after 18:00.

## Verification reflection

The model got the time-of-day filter, grouping by machine, and descending sort right. The query ran and returned three results. I profiled it and saw SCAN readings, so SQLite checks the table rows. To test how the answer could go wrong, I replaced the time filter with LIKE '%18%'. The different averages and ranking showed that searching for those characters anywhere in the timestamp is not the same as checking the hour. I verified the result by running both queries against the same database.

Note: Query times and results can vary slightly between runs.
