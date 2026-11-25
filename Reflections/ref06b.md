# Reflection 6b

The JSON plans were the part that stood out to me. Both queries found 334 Fanuc devices. SQLite used the index with json_extract and scanned the table with the shorter ->> expression. I'd check both the results and the plan if an AI suggested that change.

For dashboard sessions I would use a small SQLite table. One thing I found interesting was that shelve also used SQLite on my laptop. The timings compared the two ways of using it on this machine.

I had AI help with the lab and the server test. At first I didn't understand why connection B still showed reset. A's change was still in an open transaction. The lock record showed B waiting for A, and the screenshot shows B's update after A committed. For my project I want to work on machine maintenance and parts costs. One thing I'd ask my pod is when an optional JSON field should have its own column.
