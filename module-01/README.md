# Module 1 — Databases and local-first data

This page collects my Module 1 notes and evidence for the HSBI Databases course.

## Learning goals

In this module, I am learning to:

- Explain the course’s challenge- and project-based learning approach and portfolio assessment.
- Create and maintain a personal GitHub portfolio.
- Set up and verify the Python, SQLite, DuckDB, and Datasette toolchain with `uv`.
- Compare embedded databases with client/server databases using measurements.
- Load data into SQLite and query it from Python.
- Run an LLM-generated SQL query, then verify its result and query plan.

## Setup and SQLite shell

- [Toolchain verification](uv-check.txt)
- [SQLite shell tour](shell-tour.txt)
- [SQL dump for rebuilding the shell-tour database](tour.sql)

## Telemetry exercise

The scripts generate two days of machine readings and load them into a local SQLite database:

1. Generate the CSV: `uv run python module-01/generate_telemetry.py`
2. Load the database: `uv run python module-01/load_telemetry.py`

The generated dataset contains **172,800 readings**. The local database measured **10 MB**. The database and generated CSV are excluded from Git; the scripts can recreate them.

The script files are [generate_telemetry.py](generate_telemetry.py) and [load_telemetry.py](load_telemetry.py). Screenshots of the generator, query results, and row count are in the [evidence gallery](evidence/README.md).

## Reflection

- [Reflection 1](../Reflections/ref01.md)

## To add as I continue the module

- Notes on the course inspirations and my personal profile
- My definition of IoT, including domains, protocols, devices, and challenges
- Results and timings for the three telemetry queries
- [LLM query verification notes](llm-verification.md) — prompt, SQL, run results, query plan, and verification reflection
