# SQL Island

1. The game helped me see how to ask for one piece of information at a time. For example, I can start with all inhabitants and narrow the result to friendly people with a job ending in “smith.”
2. I used `SELECT`, `WHERE`, `AND`, `LIKE`, `INSERT`, and joins. To get Stranger's ID, I would select `personid` from `inhabitant` and filter by `name = 'Stranger'`. To get Onionville's chief, I would match `village.chief` with `inhabitant.personid` and select the inhabitant's name.
3. A table is a collection of similar records. A row is one record, such as an inhabitant. A column is one detail about it, such as the person's job. A query is the instruction I give the database to find the records and details I need.
4. I was surprised that joining by village ID and joining by the chief's person ID answer different questions. The first can tell me who lives there. The second can tell me who the chief is. Picking the right columns to join was the part I found least obvious.

My pod helped me get started with the game. I lost the later progress view when the page refreshed. [Reflection 1](../Reflections/ref01.md)
