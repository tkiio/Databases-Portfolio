# Module 4 — Integrity at the edge

This module makes a local SQLite database check its own data. A faulty sensor or a replayed CSV should not silently create invalid or duplicate readings.

## Learning goals

By the end of this module, you can:

1. Create tables with `NOT NULL`, `UNIQUE`, `CHECK`, `PRIMARY KEY`, `FOREIGN KEY`, and `STRICT` typing.
2. Use generated columns to derive values in the database engine.
3. Write triggers that enforce rules and maintain alarm/audit tables automatically.
4. Use DML, including `UPSERT ... ON CONFLICT`, for ingestion without duplicate readings.
5. Explain how server access control differs from permissions and read-only connections in a local SQLite application.

## What is ready

| Task | Evidence | Status |
| --- | --- | --- |
| A: unconstrained/guarded tables, NULL and type experiments | [Study notes](integrity-notes.md), [actual output](evidence/acceptance.txt) | Automated experiment complete; personal/pod study still to record |
| B: share with another pod | [Discussion section](integrity-notes.md#agreed-learning-pod-discussion) | Not yet — requires the actual discussion |
| 1: prove constraints and generated arithmetic | [Setup SQL](setup.sql), [rejections and generated value](evidence/constraints.txt) | Complete |
| 2: UPSERT and CSV replay | [UPSERT](upsert.sql), [Python loader](ingest.py), [synthetic fixture](readings.csv), [double-run counts](evidence/upsert.txt) | Complete |
| 3: alarms, audit and measured cost | [Trigger DDL](triggers.sql), [alarm/audit output](evidence/triggers.txt), [benchmark](bench.py), [measurements](evidence/trigger-cost.txt) | Complete, including deliberate counterexamples |
| 4: view and access control | [View SQL](machine_health.sql), [commands and outcomes](evidence/access-control.txt), [comparison](integrity-notes.md#access-control-comparison) | Complete |
| 5: optional BEFORE/AFTER comparison | [Explanation](trigger-variant.md), [script](trigger_variant.py), [output](evidence/trigger-variant.txt) | Complete |
| Reflection | [Reflection 4 draft](../Reflections/ref04.md) | Draft — add personal experience after reviewing/reproducing |

The scripts and captured results were prepared and run with Codex on this laptop. They demonstrate program behaviour; they do not claim that I completed a pod discussion or personally ran each command. The CSV is synthetic test data, not real plant telemetry.

## Reproduce everything

Use the terminal in the repository root, with the existing `uv` environment and `sqlite3` available:

```sh
uv run python Module04/run_lab.py
```

The script builds `edge.db`, executes the experiments, records exact errors and results in `evidence/`, measures two 10,000-row trigger workloads, and runs the optional trigger comparison. It enables foreign keys for every database-writing connection. An existing `edge.db` makes it stop, so it cannot silently erase an earlier lab.

To deliberately rebuild **this module's lab data** and refresh its evidence:

```sh
uv run python Module04/run_lab.py --reset
```

`--reset` erases the lab tables and their contents. Independent reruns of the smaller experiments are:

```sh
uv run python Module04/ingest.py
uv run python Module04/bench.py
uv run python Module04/trigger_variant.py
```

The loader assumes the schema, sensors and unique index have already been created by `run_lab.py`. Running the loader after the full lab may update the deliberately changed test values, and the course audit trigger logs replayed updates. Use a full rebuild to reproduce the saved sequence exactly.

## Read the database

```sh
sqlite3 Module04/edge.db
```

Then enter these at the SQLite prompt:

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

`edge.db` is a binary database: inspect it with SQLite rather than editing it as text in VS Code. The final demonstration contains five readings, one alarm, and three audit entries, including the intentional counterexamples.

## Key findings to explain

- `CHECK` alone accepts `NULL`; use `NOT NULL` when a value is required.
- `STRICT` accepts a numeric string if it can convert it without losing information.
- A replay leaves reading counts unchanged because `(sensor_id, ts)` is unique.
- The course alarm handles inserts only; an UPSERT update can miss it.
- The sample audit logs unchanged values and can be edited by a writer. It is not immutable.
- `energy_j = value * interval_s` demonstrates generated arithmetic. For these temperature/vibration/load metrics, the result is not physically an energy measurement.
- A read-only connection blocks writes but still permits direct reads of base tables.

See the [study notes](integrity-notes.md) for explanations, sources, and remaining questions.

## What goes into Git

Commit the `.sql`, `.py`, `.md`, evidence `.txt` files and the small synthetic `readings.csv`. Keep `edge.db`, its journal/WAL files, `.venv/` and `.env` out of Git. The database is rebuilt from the scripts; the evidence records what actually happened.

[Portfolio home](../README.md) · [Reflections](../Reflections/README.md) · [Course materials](https://github.com/iotempire/iotempire-teaching/tree/main/full-classes/hsbi-databases-10d)
