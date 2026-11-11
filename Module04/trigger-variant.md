# Task 5 — BEFORE versus AFTER alarms

The [experiment script](trigger_variant.py) compares the two timings in separate, fresh in-memory databases. The [captured output](evidence/trigger-variant.txt) contains the trigger definitions, actual results, and exact errors. Run it from the repository root with `uv run python Module04/trigger_variant.py`.

| Experiment | BEFORE INSERT | AFTER INSERT |
| --- | --- | --- |
| Insert a valid 2.7 mm/s vibration reading | One alarm | One alarm |
| Count readings inside the alarm trigger | 0 | 1 |
| Insert an invalid value of 9000 | CHECK rejects it; no extra persisted alarm | CHECK rejects it; no extra persisted alarm |
| Reject using a separate `RAISE(ABORT, ...)` trigger | Rejected; zero readings persist | Rejected; zero readings persist |

Changing the timing did not change the successful alarm's values. The probe explains the difference: BEFORE runs before the new reading is in the table; AFTER sees it there. The invalid insert left the reading, alarm, and probe counts unchanged in both variants. A BEFORE trigger's changes are not independently committed; statement failure can roll them back. This result does not establish whether the BEFORE trigger ran before that CHECK was evaluated.

AFTER is a sensible default for recording an alarm about a row that has been inserted. It is still part of the same statement and transaction, so it does not mean the row is permanently committed. BEFORE is useful for rejecting an incoming row with `RAISE(ABORT)`, although the last experiment demonstrates that AFTER can also reject and undo that insert.

The script supplies `reading_id = 1` explicitly. SQLite documents that `NEW.rowid` is undefined in a BEFORE INSERT trigger when an integer rowid was not explicitly supplied. It also cautions about BEFORE triggers that modify the very row the outer statement is changing. [SQLite CREATE TRIGGER documentation](https://www.sqlite.org/lang_createtrigger.html#cautions_on_the_use_of_before_triggers).

These are automated experiments prepared with Codex; they are not evidence of a pod discussion. The original lab alarm is still insert-only: switching BEFORE/AFTER does not make it handle an UPSERT's UPDATE branch.
