# Reflection 6a

The race between SQLite and DuckDB was the most interesting part for me. DuckDB was much faster at grouping the history. The small write and lookup tests helped me see why I would still keep SQLite for saving repairs and parts in my project.

I had trouble with the folder name and the virtual environment at first. The monthly query was another good example. It ran in SQLite, but the date arguments were in the wrong order and I got NULL for the month. I used AI help with the benchmark and checked that both engines returned the same results before comparing times.

The refresh check compared the number of rows and the price total. It caught the deliberately wrong copy. My question for the pod is how old a report can be before we should check the current data instead.
