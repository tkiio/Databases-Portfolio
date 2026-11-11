# Task 5 — BEFORE and AFTER triggers

The result I want to remember is that changing an alarm from `AFTER INSERT` to `BEFORE INSERT` can still produce the same alarm. The difference is when the trigger runs and what it can see in the table.

The [comparison script](trigger_variant.py) uses a separate temporary in-memory database for each version. The [saved output](evidence/trigger-variant.txt) shows the SQL, results and error messages. To repeat it from the portfolio's main folder:

```sh
uv run python Module04/trigger_variant.py
```

| Experiment | BEFORE INSERT | AFTER INSERT |
| --- | --- | --- |
| Insert a valid vibration reading of 2.7 mm/s | One alarm | One alarm |
| Count readings from inside the alarm trigger | 0 | 1 |
| Insert an invalid value of 9000 | CHECK rejects it; no extra alarm remains | CHECK rejects it; no extra alarm remains |
| Reject with a separate `RAISE(ABORT, ...)` trigger | Rejected; zero readings remain | Rejected; zero readings remain |

The count makes the timing easier to explain. BEFORE sees zero readings because the new row has not been inserted yet. AFTER sees one because the row is already in the table. Both versions created the same successful alarm.

The invalid insert left the reading, alarm and count-check tables unchanged. Trigger changes are part of the same statement and can be rolled back when it fails. This result alone does not tell me whether the BEFORE trigger ran before SQLite checked that invalid value.

For this alarm, AFTER is a sensible choice because it records an alarm for a reading that has been inserted. AFTER still runs inside the transaction, so it does not mean the data has been permanently committed. BEFORE can reject a row with `RAISE(ABORT)`, but the last test shows that AFTER can also reject and undo the insert.

One detail to keep in mind is that the script supplies `reading_id = 1`. SQLite says `NEW.rowid` is undefined in a BEFORE INSERT trigger if the integer row ID was not supplied. It also warns about BEFORE triggers that change the same row the original statement is changing. [SQLite trigger documentation](https://www.sqlite.org/lang_createtrigger.html#cautions_on_the_use_of_before_triggers)

Changing BEFORE to AFTER also does not solve the UPSERT problem from Task 3. An INSERT trigger still does not cover an UPSERT that takes the UPDATE branch.
