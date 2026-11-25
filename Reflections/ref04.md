# Reflection 4

The part I want to remember is that CHECK and NOT NULL do different things. A CHECK can let NULL through, so I need a separate rule when a value is required. The CSV task also made UPSERT clearer. The table went from one reading to four and stayed at four when the file was loaded again.

I found this module a bit difficult. My pod mates and I helped each other work through the material. I used AI help with the scripts and checked the behaviour against the saved errors and row counts. The trigger surprised me because it worked for a new high reading, but the update part of an UPSERT could miss it. I'd ask my pod if a correction should raise an alarm too.
