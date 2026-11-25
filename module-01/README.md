# Module 1 — Databases and local-first data

This page collects my Module 1 notes and evidence for the HSBI Databases course.

## Personal profile
I am Trevor Kiio. 20 year old student at HSBI taking Mechatronics and Automation. I am Kenyan and have interacted, though minimally with HTML, C and C++. I have also done a bit of app development but with great help from AI moreso Claude and ChatGPT. This has helped me understand a great deal of database and made sense of the stuff that await me in this class. I am really looking forward to go through with this class.

## Learning goals
By the end of this module, you can:

Explain how this class works — the CBL/PBL philosophy, the portfolio-based project work assessment, and the "moving bar" of a first-time course.

Set up your personal GitHub portfolio from the course template, with a clean first commit and a .gitignore that keeps databases and secrets out of Git.

Set up the entire toolchain reproducibly with uv — one fixed Python plus SQLite, DuckDB, Datasette, and more — on Windows, macOS, or Linux, and verify it.

Explain — with a measurement, not a slide — the difference between an embedded database and a client/server database, and why most local apps should not run a server.

Load real rows into SQLite and query them from Python using bound parameters.

Take a first LLM-generated query, run it, and begin the habit that defines this course: verify before you trust.

## Setup and SQLite shell

- [Toolchain verification](uv-check.txt)
- [SQLite shell tour](shell-tour.txt)
- [SQL dump for rebuilding the shell-tour database](tour.sql)

I find `.schema` useful because it tells me how the table was defined before I start writing a query.

## Telemetry exercise

The scripts generate two days of machine readings and load them into a local SQLite database:

1. Generate the CSV: `uv run python module-01/generate_telemetry.py`
2. Load the database: `uv run python module-01/load_telemetry.py`

The generated dataset contains 172,800 readings. The local database measured 10 MB. The database and generated CSV are excluded from Git; the scripts can recreate them.

The script files are [generate_telemetry.py](generate_telemetry.py) and [load_telemetry.py](load_telemetry.py). The [timed SQLite queries](evidence/telemetry-queries.txt) show the counts and maximum vibration. [query_telemetry.py](query_telemetry.py) reads the same file with a bound threshold. Screenshots are in the [evidence gallery](evidence/README.md).

The 172,800 readings fit in a local 10 MB file. SQLite can query it from the app without running a separate service. A shared PostgreSQL server is useful when several people need the same central data, as in the [two-writer exercise](../Module06b/README.md#concurrency-result). A hosted database would add service costs that the team operating it would pay, even for this small dataset.

## Reflection

- [Reflection 1](../Reflections/ref01.md)

## Study notes and links

- [SQL Island](sql-island.md) — tutorial answers from the game examples.
- [LLM query verification](llm-verification.md) — prompt, result, plan and counterexample.
- [Course syllabus](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/syllabus.md) and [Module 1 handout](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/modules/01-introduction-and-local-first.md).
- Pod portfolios for [Ryan](https://github.com/reilly-codes/Database-class) and [Trevor Fidel](https://github.com/TrevorFidel/Database-HSBI).
