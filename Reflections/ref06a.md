# Reflection 6a

The most interesting part of this module for me was the race between SQLite and DuckDB. The timings made the difference between the two engines easy to see. My main takeaway is that the type of work matters: reading and grouping a large history is different from handling lots of small inserts and lookups.

The timing table shows the same queries with matching answers, warm-up runs and repeated measurements. The monthly query also needed a correction because SQLite expects the format first in strftime. The old query ran without an error but did not group the months correctly. I want to remember that getting an answer quickly is not enough if it is answering a different question.

I had some problems with file names, saving the code and the virtual environment warning while getting started. A space in the folder name made Python look for the wrong file, and an empty script ran without doing anything. Checking the path and saving the file helped. Reading the plans also made the race easier to understand: DuckDB used a hash group operation, while SQLite used a table scan and a temporary B-tree for grouping.

Codex helped me with the benchmark scripts and reading the plans. The refresh checks compared the row counts and price sums, and the deliberately wrong copy failed. The compression test gave a smaller file with similar warm read time. For my maintenance project, I would save new repairs and parts in SQLite. If we later need longer cost reports, I would use a separate copy and make its refresh time visible. My question for the pod is how old that copy can be before it is too stale to use.
