# Integrity notes — Module 4

These notes accompany assistant-run experiments on this laptop. I still need to review/reproduce the results and record my own pod discussion. The outputs are linked below so the claims can be checked.

## Sources and the concept each explains

| Source | Concept used here |
| --- | --- |
| [SQLite CREATE TABLE](https://sqlite.org/lang_createtable.html#check_constraints) | `CHECK` rejects zero/false; NULL is not a failure. `NOT NULL` must express required values separately. |
| [SQLite STRICT tables](https://sqlite.org/stricttables.html) | Lossless type conversion still occurs; `'41.5'` can become REAL, but `'hot'` cannot. |
| [SQLite foreign keys](https://sqlite.org/foreignkeys.html#fk_enable) | Each connection must enable enforcement before its transaction; a referenced sensor must exist. |
| [SQLite generated columns](https://sqlite.org/gencol.html) | A VIRTUAL value is computed when read; a STORED value is computed when written. The expression, rather than a supplied value, controls the column. |
| [SQLite UPSERT](https://sqlite.org/lang_upsert.html) | A unique key identifies a replay and `excluded.value` is the proposed new value. An UPSERT is not a way around other constraints. |
| [SQLite triggers](https://sqlite.org/lang_createtrigger.html) | INSERT and UPDATE are separate events, and trigger work participates in the surrounding statement/transaction. |
| [SQLite URI filenames](https://sqlite.org/uri.html) and [query_only](https://sqlite.org/pragma.html#pragma_query_only) | `mode=ro` prevents connection writes; `query_only` is a connection setting. |
| [SQLite omitted SQL features](https://sqlite.org/omitted.html) | SQLite has no database-user `GRANT`/`REVOKE` permission model. |
| [PostgreSQL GRANT](https://www.postgresql.org/docs/current/sql-grant.html) | Server roles can receive privileges on particular database objects. |

## Things looked up

The documentation questions above were checked with AI assistance. No personal Google searches are being claimed here.

- Does `CHECK` reject NULL? No: the expression evaluates to NULL and the row passes unless `NOT NULL` also applies. [Source](https://sqlite.org/lang_createtable.html#check_constraints)
- Does STRICT reject every quoted number? No: losslessly convertible text numbers are accepted. [Source](https://sqlite.org/stricttables.html)
- Does an INSERT alarm fire on an UPSERT's UPDATE branch? No: that branch is an UPDATE and requires an UPDATE trigger for equivalent coverage. [Source](https://sqlite.org/lang_createtrigger.html)
- Does an audit-writing trigger make its table immutable? No: it only writes audit rows; it does not remove a writer's ability to edit the audit table. [Source](https://sqlite.org/lang_createtrigger.html)

## The three integrity layers

| Layer | Meaning | Concrete proof |
| --- | --- | --- |
| Entity | Rows are identifiable and required fields are present. | Repeated `sensor_id`, repeated machine/metric and NULL timestamp fail. |
| Referential | A relationship points to an existing row. | A reading for sensor 99 fails with `FOREIGN KEY constraint failed`. |
| Semantic/domain | Values obey the rules of the application. | `9000`, `'hot'`, unknown metric and zero interval fail range/type/domain rules. |

`CHECK` cannot query another table using a subquery. Use a foreign key for sensor existence, and triggers for appropriate rules involving other rows/tables.

## Task A — what the database accepted

The unconstrained table accepted all three supplied junk rows: a temperature of 9000, the text `'hot'` in a REAL-affinity column, and metric `'bogus'` with value -500. Its `typeof(value)` output shows that `'hot'` was actually stored as text. [Actual acceptance/rejection transcript](evidence/acceptance.txt)

The guarded table rejected those rows one at a time, so one failure did not hide the others. Extra probes found:

- `CHECK(value BETWEEN -273.15 AND 5000)` accepted NULL in a nullable test column; `NOT NULL` rejected it in the guarded table.
- `'41.5'` was accepted and stored as REAL under STRICT.
- A duplicate primary key was rejected, while supplying NULL to an `INTEGER PRIMARY KEY` allocated an ID automatically.
- A UNIQUE pair with a nullable component accepted two `('cnc-01', NULL)` rows. The lab's NOT NULL columns prevent that gap.
- `120` passed the broad temperature range, even though it could be a faulty reading for a particular machine. A plausible value is not proof of sensor accuracy.

These are the remarkable findings to explain to the other pod. Their reactions have not yet been recorded.

## Task 1 — rejection and generated-column proof

[setup.sql](setup.sql) defines both STRICT tables. [constraints.txt](evidence/constraints.txt) records each statement and the exact Python SQLite exception message:

| Probe | Result |
| --- | --- |
| `value=9000` | Range CHECK rejects it. |
| `value='hot'` | STRICT rejects TEXT in `reading.value`. |
| `sensor_id=99` | Foreign key rejects it. |
| A second `('cnc-01','temp_c')` sensor | Composite UNIQUE rejects it. |
| Reuse `sensor_id=1` | Primary-key uniqueness rejects it. |
| `ts=NULL` | NOT NULL rejects it. |
| `interval_s=0` | Interval CHECK rejects it. |
| `metric='bogus'` | Allowed-metric CHECK rejects it. |
| Supply `energy_j` directly | SQLite rejects an INSERT into the generated column. |

The initial valid row returns `41.5 * 1 = 41.5` in `energy_j`, without supplying that column in the INSERT. That proves the engine computes the expression. It does **not** prove a physically meaningful energy value: temperature times seconds is not joules. Watts times seconds gives joules; watts times seconds divided by 3,600,000 gives kWh. The supplied expression/name was retained to match the assignment, with this limitation recorded.

The broad range is also not a metric-specific rule: it does not separately prohibit negative vibration or restrict spindle load to a chosen percentage range. Timestamp TEXT is required but not checked for calendar validity.

## Task 2 — why replay does not duplicate readings

The unique `(sensor_id, ts)` index makes one reading per sensor/timestamp enforceable. [upsert.sql](upsert.sql) changes the initial value from 41.5 to 41.7 while keeping one row for that key. [ingest.py](ingest.py) reads the synthetic CSV, enables foreign keys on its own connection, and uses bound values with `executemany` inside one transaction.

The [saved double-run proof](evidence/upsert.txt) shows **1 → 4 → 4 readings**. A deliberately bad CSV then contained a valid new row followed by sensor 99: its foreign-key error rolled back the entire file, keeping the count at four.

This establishes idempotence of the reading rows for this fixture, not every side effect. The course UPSERT updates only `value`; a changed incoming `interval_s` would be ignored. Once the audit trigger exists, replayed updates also append audit rows even when a reading value is unchanged. A production version could update all intended fields and avoid unchanged updates, for example with a suitable `DO UPDATE ... WHERE` condition.

## Task 3 — alarms and audit

[triggers.sql](triggers.sql) retains the course trigger definitions. A new 2.7 mm/s vibration at 09:00 created an alarm automatically. Updating that particular row to 1.4 created an audit row showing old/new values `(2.7, 1.4)`. Only that demonstration row was targeted, so the other CSV rows were preserved. [Actual trigger output](evidence/triggers.txt)

The negative tests matter:

1. `SET value=value` still produced a second audit row. `AFTER UPDATE OF value` means the column is named in the update; it does not mean the value changed. A condition such as `WHEN OLD.value IS NOT NEW.value` can suppress this noise.
2. The CSV's low vibration reading was corrected upward to 2.8 by UPSERT. There was still only one alarm, because the supplied alarm handles INSERT, not UPDATE. An extra UPDATE trigger with an appropriate threshold-crossing condition is needed for that policy.
3. An ordinary `UPDATE audit` succeeded. It was rolled back after demonstrating the gap. The sample does not make the audit immutable. Rejection triggers could prohibit ordinary UPDATE/DELETE operations, but someone allowed to change the schema could remove those guards.

The final demonstration has five readings, one alarm and three audit entries. This is evidence of the course example's behaviour, including its gaps, rather than a claim that it is a complete production alarm system.

### Trigger cost

[bench.py](bench.py) measures 10,000 rows per transaction on fresh, temporary file databases. Both cases have the same schema, unique index, rows, journal and synchronous settings. It times insertion **and commit**, excluding setup, row construction and connection creation. It performs one warm-up per case and five measured runs, alternating order, then reports medians.

[trigger-cost.txt](evidence/trigger-cost.txt) contains every measured time and the median comparison for each workload:

- `1.4 mm/s`: the alarm condition is evaluated, with no alarm rows written.
- `2.7 mm/s`: all 10,000 inserts write alarm rows, so the measured cost includes that extra work.

The trigger increased median ingest time in the recorded run. Its cost depends on the workload and machine; the firing case includes creating and storing 10,000 alarms, not just evaluating a condition. Python's SQLite library and the CLI have different version numbers here, so both are recorded and the benchmark uses Python consistently.

## Access control comparison

PostgreSQL authenticates roles and can grant SELECT on a reporting view while withholding privileges on its base tables. SQLite has no database-user GRANT model, so this local demonstration controls access through file permissions and read-only connections. That is reasonable for a gateway managed by a trusted local account, although `chmod 444` makes the file readable by everyone and its owner can restore writes. A shared multi-tenant web application needs account/tenant authorization that permissions on one common database file do not provide. [PostgreSQL privileges](https://www.postgresql.org/docs/current/sql-grant.html), [SQLite limitations](https://sqlite.org/omitted.html)

[machine_health.sql](machine_health.sql) groups readings into a report. The [access-control transcript](evidence/access-control.txt) proves that reads succeeded, file mode 444 blocked a DELETE, `mode=ro` blocked a DELETE even after the file became writable again, and `PRAGMA query_only=ON` blocked another DELETE. It also shows a read-only connection reading `reading` directly: a view is a report interface, not a security boundary when the reader has unrestricted access to the same database. Original file permissions were restored after the experiment.

## Task 5 — timing variant

The [BEFORE/AFTER comparison](trigger-variant.md) found the same final alarm in both cases. An extra probe saw zero reading rows inside BEFORE and one inside AFTER. Both can reject using `RAISE(ABORT)`, and a failed statement leaves no extra persisted alarm. AFTER means after the row operation, not after transaction commit. [Actual output](evidence/trigger-variant.txt)

## AI assistance and verification

The request to Codex was **“do everything”**, following the pasted Module 4 instructions. Codex generated these SQL/Python scripts and notes, ran them locally and saved actual output. An automated review also checked the approach against official SQLite documentation.

The proposed claims were checked against successful inserts, exact rejected-statement errors, duplicate-key counts after two imports, transaction rollback after a bad CSV, generated arithmetic, alarm/audit rows, failed read-only DELETEs, and repeated trigger timings. The stronger claims in the handout were qualified where the experiments or definitions did not support them: meaningful energy units, immutable audit, all-event alarm coverage, and views as access control. This is AI verification evidence; it is not a claim that the student has already reproduced the experiments or mastered the material.

Questions to practise explaining:

- Why does a CHECK accept NULL, and what closes that gap? Reproduce the two NULL tests in acceptance.txt.
- Which integrity rule cannot be replaced by the range CHECK? The missing-sensor foreign key is demonstrated in constraints.txt.
- How can a valid UPSERT fail to produce an alarm? Reproduce the UPDATE-branch counterexample in triggers.txt.
- Can AFTER reject a row? The optional variant proves that RAISE(ABORT) rejects at either timing.

## Agreed learning (pod discussion)

**Not yet.** Add the actual pod members, the neighbouring pod, the points jointly agreed, any remaining disagreement and what changed after feedback. Do not describe these prepared notes as a discussion that has already happened.

Suggested question to take to the pod/instructor: should an above-threshold correction create an alarm, and should the alarm table record only threshold crossings or every high sample? No Discord message has been posted on the student's behalf.

[Module 4 overview](README.md) · [Reflection 4 draft](../Reflections/ref04.md)
