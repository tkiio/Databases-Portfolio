# Reflection 4

My main takeaway from this module is that a database needs rules to protect the data being stored in it. Creating tables and inserting values is only part of the work. Primary keys, foreign keys and constraints help make sure that rows can be easily identified, relationships point to something that exists, and values follow the expected rules. I want to remember that CHECK and NOT NULL do different things, because a CHECK on its own can still allow NULL.

The useful part of the lab was connecting each rule to a concrete result. The CSV example shows how UPSERT can keep the row count the same when the same file is loaded twice. The trigger examples also show why it matters to check the exact operation: the alarm worked for a new high reading, but an UPSERT update could miss it. An unchanged value could still create an audit entry. These are things I would want to check before assuming that the code works in every situation.

Understanding the content was a bit difficult for me. My pod mates and I helped each other understand it, and working through the concepts together was helpful. I also helped them with the content, so we were learning from one another.

I got some help from Codex with the lab scripts and reading the results. The saved evidence includes the rejected statements and their errors, the row counts after loading the CSV twice, the alarm and audit rows, and the read-only tests. My advice to myself is to use those results to check an AI suggestion and practise explaining why it behaves that way. One question I still want to discuss with my peers or instructor is how an alarm should behave when an existing reading is corrected and goes above the set threshold.
