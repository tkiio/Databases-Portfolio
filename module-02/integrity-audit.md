# Integrity audit of the legacy database

The runnable queries are in [`integrity-audit.sql`](integrity-audit.sql). The timings below came from the SQLite shell on this laptop; they may vary between runs.

## 1. Orphan maintenance job

**Query result:** `job_id = 3`, `machine_name = cnc-05`.

**Production impact:** This job cannot be linked to a machine or its site, so maintenance history and reporting by location can be wrong.

## 2. Duplicate natural key

**Query result:** `P-1003` has 2 copies.

**Production impact:** Joining by part number can duplicate job rows, and the database cannot reliably identify one part record.

## 3. Price stored as text

The text comparison `unit_price < '15'` returns only `P-1001` at `12.50`. The numeric comparison using `CAST(unit_price AS NUMERIC) < 15` also returns both duplicate `P-1003` rows at `9.90`.

**Production impact:** Text ordering can omit cheaper parts from invoice or inventory calculations.

## 4. Installation date stored as free text

**Query result:** `RANDOM-NAME` has `installed = unknown`.

**Production impact:** Invalid values cannot be reliably sorted, filtered, or used in date calculations. The supplied GLOB query checks the text shape only; it does not validate real calendar dates.

## 5. Comma-separated parts list

The join returns job 2 twice (because `P-1003` is duplicated) and job 3 once. It silently omits job 1, which lists `P-1001,P-1002` together.

**Production impact:** A report using this join loses multi-part jobs and may double-count jobs that happen to contain one part number.

## Captured results

```text
Orphan jobs:
job_id  machine_name
3       cnc-05

Duplicate part numbers:
part_no  copies
P-1003   2

Text comparison (< '15'):
part_no  unit_price
P-1001   12.50

Numeric comparison (CAST(...) < 15):
part_no  unit_price
P-1001   12.50
P-1003   9.90
P-1003   9.90

Malformed date text:
machine_name  installed
RANDOM-NAME   unknown

Naive list join:
job_id  description
2       Coolant filter
2       Coolant filter
3       Ball bearing 6203
```
