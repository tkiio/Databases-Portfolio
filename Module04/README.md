# Module 4 — Integrity at the edge

In this module, my focus is on how a database checks the data it receives. The main idea I want to remember is that creating a table is only the beginning. It also needs rules that reject invalid values and stop duplicate readings.

## Learning goals

By the end of this module, you can:

1. Create tables with `NOT NULL`, `UNIQUE`, `CHECK`, `PRIMARY KEY`, `FOREIGN KEY`, and `STRICT` typing.
2. Use generated columns to derive values in the database engine.
3. Write triggers that enforce rules and maintain alarm/audit tables automatically.
4. Use DML, including `UPSERT ... ON CONFLICT`, for ingestion without duplicate readings.
5. Explain how server access control differs from permissions and read-only connections in a local SQLite application.

## My work and evidence

| Task | My files and results |
| --- | --- |
| A: compare a table with and without constraints | [Integrity notes](integrity-notes.md), [accepted and rejected rows](evidence/acceptance.txt) |
| B: exchange findings with another pod | [Pod discussion](integrity-notes.md#agreed-learning-pod-discussion) — neighbouring-pod feedback still to add |
| 1: prove the constraints work | [Setup](setup.sql), [exact errors and generated value](evidence/constraints.txt) |
| 2: load a CSV twice without duplicates | [UPSERT SQL](upsert.sql), [Python loader](ingest.py), [sample CSV](readings.csv), [row counts](evidence/upsert.txt) |
| 3: alarms, audit and trigger cost | [Triggers](triggers.sql), [alarm and audit results](evidence/triggers.txt), [benchmark](bench.py), [timings](evidence/trigger-cost.txt) |
| 4: access control | [Reporting view](machine_health.sql), [read-only results](evidence/access-control.txt), [comparison with PostgreSQL](integrity-notes.md#access-control-comparison) |
| 5: optional BEFORE/AFTER comparison | [My explanation](trigger-variant.md), [script](trigger_variant.py), [results](evidence/trigger-variant.txt) |
| Reflection | [Reflection 4](../Reflections/ref04.md) |

The CSV is a small generated example for the lab.

## What I want to remember

- `CHECK` and `NOT NULL` do different jobs. A CHECK by itself can still allow NULL.
- A foreign key makes sure the sensor exists before its reading is accepted.
- The unique sensor/timestamp pair stops a replay from creating another reading.
- INSERT and UPDATE are different events, so an insert-only alarm can miss an UPSERT update.
- A trigger adds work to each write. The timings show why that cost matters.
- A read-only connection prevents changes, but it can still read the underlying tables.

## Running my lab

From the portfolio's top folder:

```sh
uv run python Module04/run_lab.py
```

This creates `edge.db` and saves the results in `evidence/`. If the database already exists, the script stops. To rebuild the lab and replace its existing data:

```sh
uv run python Module04/run_lab.py --reset
```

I can also run the loader, benchmark and optional experiment separately:

```sh
uv run python Module04/ingest.py
uv run python Module04/bench.py
uv run python Module04/trigger_variant.py
```

The loader needs the tables, sensors and unique index created by the full lab. Running it afterwards can update the test values again and add audit entries. A full rebuild reproduces the saved sequence.

## Opening the database

```sh
sqlite3 Module04/edge.db
```

At the SQLite prompt:

```sql
PRAGMA foreign_keys = ON;
.headers on
.mode box
.tables
SELECT * FROM reading;
SELECT * FROM alarm;
SELECT * FROM audit;
SELECT * FROM machine_health;
.quit
```

The final lab contains five readings, one alarm and three audit entries. I need to open the `.db` file through SQLite because it is a binary database file.

## Files to commit

The scripts, notes, evidence text files and small sample CSV belong in the portfolio. `edge.db`, its journal files, `.venv/` and `.env` stay out of Git. The scripts let someone rebuild the database.

[Portfolio home](../README.md) · [My notes](integrity-notes.md) · [Reflection 4](../Reflections/ref04.md) · [Course materials](https://github.com/iotempire/iotempire-teaching/tree/main/full-classes/hsbi-databases-10d)
