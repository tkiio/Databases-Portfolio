# Trevor Kiio — HSBI Databases Portfolio

This repository collects my notes, exercises, reflections, and evidence from the HSBI Databases course. 
## Table of Contents

- [Module 1 ](module-01/README.md)
- [Module 2 ](module-02/README.md) 
- [Module 3](Module03/README.md)
- [Module 4](Module04/README.md)
- [Module 5](Module05/README.md)
- [Module 6a](Module06a/README.md)
- [Module 6b](Module06b/README.md)
- [Reflection 1](Reflections/ref01.md)
- [Reflection 2](Reflections/ref02.md)
- [Reflection 3](Reflections/ref03.md)
- [Reflection 4](Reflections/ref04.md)
- [Reflection 5](Reflections/ref05.md)
- [Reflection 6a](Reflections/ref06a.md)
- [Reflection 6b](Reflections/ref06b.md)
- [Hardware inventory](Hardware/README.md)

## Checkpoint 2

| Module | What I can show | What it demonstrates |
| --- | --- | --- |
| 4 | [CSV replay and rollback](Module04/evidence/upsert.txt) | The row count went from 1 to 4 and stayed at 4 on replay. A bad batch rolled back. |
| 5 | [Update and storage benchmark](Module05/benchmark-results.md) | A site change touched 1 normalized row and 4,000 report rows. |
| 6a | [SQLite and DuckDB timings](Module06a/timings.md) | The engines returned matching results, and DuckDB was much faster on the large analytical scans in this test. |
| 6b | [PostgreSQL concurrency result](Module06b/README.md#concurrency-result) and [engine decision](Module06b/README.md#task-3--my-decision-record) | B waited for A's lock, then finished after A committed. The decision record uses measurements from the labs. |

[Project ticket](Module06b/project-ticket.md) · [Reflection log](Reflections/README.md) · [Course checkpoint guidance](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/syllabus.md#how-module-points-are-earned-from-your-portfolio)

## Module 1 quick links

- [Toolchain check](module-01/uv-check.txt)
- [SQLite shell tour](module-01/shell-tour.txt)
- [Rebuildable SQL dump](module-01/tour.sql)
- [Telemetry scripts and results](module-01/README.md#telemetry-exercise)
- [Screenshots and evidence](module-01/evidence/README.md)

## Pod Members

- Ryan Reilly Oduory — [portfolio](https://github.com/reilly-codes/Database-class)
- Trevor Fidel Nyongesa — [portfolio](https://github.com/TrevorFidel/Database-HSBI)

Author : Trevor Kiio

