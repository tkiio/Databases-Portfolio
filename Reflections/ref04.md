# Reflection 4

Draft based on the automated Module 4 experiments. Review the evidence and replace the prompts below with personal experience before treating this as a finished logbook entry.

The main takeaway to remember is that rules belong in the database as well as in application code. The experiments show different responsibilities: keys identify rows, foreign keys protect relationships, and checks restrict values. A surprising result is that CHECK alone accepts NULL, while STRICT still accepts a numeric string if SQLite can convert it without losing information. The rejection messages make those differences concrete.

The CSV replay kept the reading count at four after both imports because sensor and timestamp form a unique key. The alarm and audit experiments show why it is necessary to test the exact event: an INSERT alarm missed an UPSERT update, and an unchanged value still created an audit entry. Read-only access prevented deletion, but it did not hide the underlying tables. These are useful reminders to verify an AI-generated claim with a counterexample instead of relying only on code that runs successfully.

What worked well for me: [add one experiment I personally reproduced and what helped me understand it]. What was difficult: [add the error, concept or command I struggled with, and what helped]. A useful exploration: [describe one result I found surprising after checking it myself].

Help and interaction: Codex prepared and ran the supplied experiments and drafted the notes. [Add who in my pod or the teaching team helped me, what feedback was valuable, and who I helped; say none if appropriate.] [Add any extra contribution or class presentation I actually made.] A question to discuss is whether a corrected vibration reading that crosses the threshold should create a new alarm, and how unchanged replays should affect the audit trail.
