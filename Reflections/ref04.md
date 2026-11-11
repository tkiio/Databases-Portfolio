# Reflection 4

My main takeaway from this module is that the database needs rules to stop bad data from being stored. A table can accept values that do not make sense if the right constraints are missing. I want to remember that CHECK and NOT NULL do different things, because CHECK on its own can still allow NULL.

The examples show why it helps to look at the actual output. Loading the same CSV twice kept the reading count at four because of the unique key and UPSERT. The alarm worked for a new high reading, but an UPSERT update could miss it. An update that kept the same value still made an audit entry. These are useful things to check before assuming a trigger covers everything.

Understanding the content was a bit difficult for me. My pod mates and I helped each other understand it, which was helpful. I also helped them with the content, so we were learning from each other.

I got help from Codex with the SQL and Python scripts, running the experiments and understanding the results. The saved errors, row counts and trigger output were used to check what the code actually did. My question is how the alarm should work when an existing reading is corrected and goes above the threshold.
