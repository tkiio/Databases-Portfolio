# Reflection 6b

My main takeaway from this module is that the shape of the data and the way it is used should guide the database choice. A JSON document, a key/value entry and a relational row can all be stored locally, but they solve different problems. I want to remember to explain what a choice makes easier and what it costs.

The JSON plan comparison gives a clear example. Both queries returned the same 334 Fanuc devices, but json_extract used the index while the ->> shorthand scanned the table. The result is the same, but the query does not use the same expression as the index. Adding an optional vendor field did not need a new column. The constraint rejected invalid JSON, but a valid number still passed, so valid JSON is not the same as the right document structure.

For the dashboard sessions, I would choose a small SQLite key/value table. The benchmark compares 20,000 sets and gets, and the shelve backend on this laptop also uses SQLite. That makes it important to explain the API and batching differences instead of saying that one whole category of databases is faster. SQLite also allows queries across the stored sessions.

I got help from Codex with the lab scripts and the PostgreSQL test. The shared-server test also helped explain the transaction boundary. A could see its uncommitted change while B still saw reset. PostgreSQL then showed B waiting for A, and B completed after A committed. Pgweb also stayed open while a database connection failed, and queries worked again later. For my project, I want to work on machine maintenance and parts costs. One question I would ask the pod is when a vendor field should become a normal typed column. I would do that if we start relying on it for every device or need stricter validation.
