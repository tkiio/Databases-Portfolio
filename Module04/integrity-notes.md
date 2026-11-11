# Module 4 — My integrity notes

My main focus in this module is understanding how the database protects its own data. These notes connect each rule with an example and the output saved in my evidence folder.

## Sources

| Source | The concept it helps explain |
| --- | --- |
| [SQLite CREATE TABLE](https://sqlite.org/lang_createtable.html#check_constraints) | Why CHECK and NOT NULL are separate rules. |
| [STRICT tables](https://sqlite.org/stricttables.html) | Why `'hot'` is rejected but a number such as `'41.5'` can be converted and accepted. |
| [Foreign keys](https://sqlite.org/foreignkeys.html#fk_enable) | Why a reading must point to an existing sensor, and why enforcement is enabled on every connection. |
| [Generated columns](https://sqlite.org/gencol.html) | How the database calculates a value from other columns. |
| [UPSERT](https://sqlite.org/lang_upsert.html) | How to update an existing reading when the same key is replayed. |
| [Triggers](https://sqlite.org/lang_createtrigger.html) | How INSERT and UPDATE can automatically cause another action. |
| [Read-only connections](https://sqlite.org/uri.html) and [query_only](https://sqlite.org/pragma.html#pragma_query_only) | How a connection can be prevented from writing. |
| [SQLite's omitted features](https://sqlite.org/omitted.html) and [PostgreSQL GRANT](https://www.postgresql.org/docs/current/sql-grant.html) | Why access control works differently with a server. |

## Questions from the documentation

- **Does CHECK reject NULL?** No. If its result is NULL, the row passes that check. NOT NULL is needed when the value is required. [Source](https://sqlite.org/lang_createtable.html#check_constraints)
- **Does STRICT reject every quoted number?** No. SQLite can accept a string if it converts to the declared type without losing information. [Source](https://sqlite.org/stricttables.html)
- **Does an INSERT trigger cover an UPSERT update?** No. The update branch needs an UPDATE trigger for that behaviour. [Source](https://sqlite.org/lang_createtrigger.html)
- **Does an audit trigger make the audit table impossible to change?** No. The trigger records changes, but another write can still edit the audit table. [Source](https://sqlite.org/lang_createtrigger.html)

## The three layers of integrity

| Layer | How I explain it | Example from the lab |
| --- | --- | --- |
| Entity integrity | Each row has an identity and its required information. | A duplicate sensor ID or a NULL timestamp is rejected. |
| Referential integrity | A relationship must point to something that exists. | A reading for sensor 99 is rejected because that sensor does not exist. |
| Domain integrity | A value must follow the rules for that field. | A temperature of 9000 or the text `'hot'` is rejected. |

A range CHECK cannot replace a foreign key. It checks a value, while the foreign key checks whether the referenced sensor exists. SQLite also does not allow subqueries inside CHECK expressions.

## Task A — a table without rules

The table without constraints accepted all three bad examples: `9000`, `'hot'` and the unknown metric `'bogus'`. Declaring the column REAL was not enough to stop text being stored in it. [Saved output](evidence/acceptance.txt)

The constrained version rejected the bad rows separately. The results I want to remember are:

- A nullable column with a CHECK still accepted NULL.
- STRICT accepted `'41.5'` and stored it as REAL.
- A repeated primary key failed. A NULL supplied to `INTEGER PRIMARY KEY` received an automatically generated ID.
- A UNIQUE pair allowed repeated combinations containing NULL. The main sensor table avoids that with NOT NULL.
- A value of `120` passed the broad temperature rule, even though it could still be wrong for a particular machine.

The last example is a reminder that a value can pass a constraint and still be an inaccurate sensor reading.

## Task 1 — proving the constraints work

The [setup script](setup.sql) creates the two STRICT tables. The [evidence](evidence/constraints.txt) includes each rejected statement and its exact error.

| Input | Rule that rejects it |
| --- | --- |
| `value = 9000` | Range CHECK |
| `value = 'hot'` | STRICT typing |
| `sensor_id = 99` | FOREIGN KEY |
| Another sensor for the same machine and metric | UNIQUE |
| Reusing `sensor_id = 1` | PRIMARY KEY |
| `ts = NULL` | NOT NULL |
| `interval_s = 0` | Interval CHECK |
| `metric = 'bogus'` | Allowed-metric CHECK |

The valid reading produced `energy_j = 41.5 × 1 = 41.5` without that value being supplied in the INSERT. Trying to insert directly into the generated column was rejected.

There is a detail to be careful about here: temperature multiplied by time is not energy. The column demonstrates the generated calculation from the assignment, but joules would require power in watts multiplied by seconds. The broad range also does not check each metric separately, and a required TEXT timestamp does not automatically guarantee a valid date.

## Task 2 — loading the same CSV twice

The key is the combination of `sensor_id` and `ts`. The [UPSERT](upsert.sql) updates the existing reading when that combination already exists. The [Python loader](ingest.py) uses bound parameters and `executemany` to load the [sample CSV](readings.csv) in one transaction.

The [row-count evidence](evidence/upsert.txt) shows **1 → 4 → 4**: the first CSV import added the missing readings, and the second did not create duplicates. A bad CSV containing a valid row followed by sensor 99 failed, and the count stayed at four because the whole file was rolled back.

One limitation is that the supplied UPSERT changes only `value`. It would ignore a correction to `interval_s`. Also, keeping the reading count the same does not mean every side effect stays the same: once the audit trigger exists, replayed updates can still add audit entries.

## Task 3 — alarms and audit

With the [course triggers](triggers.sql), inserting a vibration reading of 2.7 created an alarm. Changing that reading to 1.4 created an audit row containing the old and new values. [Alarm and audit output](evidence/triggers.txt)

The extra examples help explain the limits:

- Updating a value to itself still created an audit entry. Naming the column in UPDATE is enough to fire this trigger. `WHEN OLD.value IS NOT NEW.value` could avoid those entries.
- An UPSERT changed a low reading to 2.8, but no new alarm appeared because the alarm only handles INSERT. An UPDATE trigger would be needed for that case.
- An UPDATE to the audit table succeeded. That change was rolled back after the example, but it shows that the audit table is not immutable just because it has an audit-writing trigger.

### Trigger cost

The [benchmark](bench.py) compares 10,000 inserts with and without the alarm trigger. It uses fresh temporary databases, one warm-up and five measured runs per case. The timing includes insertion and commit, and the comparison uses medians. [All runs and medians](evidence/trigger-cost.txt)

The lower vibration value, 1.4, checks the trigger condition without writing alarms. The higher value, 2.7, creates 10,000 alarms. In the saved results, both cases took longer with the trigger. The second case also includes the work of writing all those alarm rows, so its cost is more than just checking the threshold.

## Access control comparison

With PostgreSQL, roles can be given permission to read a view without permission to read its underlying tables. SQLite has no database-user GRANT system, so this lab uses file permissions and read-only connections. This makes sense for a local gateway managed by a trusted account, although the file owner can restore write access and mode 444 allows everyone to read the file. A web application with different tenants needs more detailed authorization than permissions on one shared file can provide. [PostgreSQL](https://www.postgresql.org/docs/current/sql-grant.html), [SQLite](https://sqlite.org/omitted.html)

The [view](machine_health.sql) gives a summary for each machine and metric. The [saved results](evidence/access-control.txt) show successful reads and rejected DELETEs with file mode 444, `mode=ro` and `query_only`. The read-only connection could still read the base table, so the view itself does not hide that data. Write permission was restored after the experiment.

## Task 5 — BEFORE and AFTER

The [optional comparison](trigger-variant.md) produced an alarm with both timings. A count taken inside the trigger was zero with BEFORE and one with AFTER, which shows when the new reading becomes visible. Both timings could reject an insert using `RAISE(ABORT)`. AFTER runs after the row operation; the transaction can still be rolled back. [Output](evidence/trigger-variant.txt)

## Checking the results

The checks include rejected inserts, loading the CSV twice, generated values, alarm and audit rows, read-only writes and repeated timings. The exact output is saved with each task.

The point I want to remember is to check what the code actually guarantees. For example, an audit trigger does not automatically make its table immutable, and an INSERT alarm does not cover every UPSERT. These examples give me concrete questions to use when checking AI suggestions.

## Agreed learning (pod discussion)

Understanding the content was a bit difficult. My pod mates and I helped each other understand it, and explaining things to one another helped with the material.

I still need to add the specific points agreed with the neighbouring pod and any question we left open. One question to discuss is whether a corrected reading that crosses the vibration threshold should create a new alarm, and whether alarms should record every high sample or only threshold crossings.

[Module 4](README.md) · [Reflection 4](../Reflections/ref04.md)
