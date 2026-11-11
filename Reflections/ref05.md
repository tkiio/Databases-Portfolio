# Reflection 5

My main takeaway from this module is that normalization reduces repeated information, but a reporting copy can make some queries faster. That copy also needs more storage and has to be kept up to date. I want to remember that fewer joins do not automatically mean a query will be faster.

The hardest part for me was naming the functional dependencies and deciding which ones were real domain rules and which were only patterns in the five rows. Drawing the two ER sketches and comparing the FD list with the model's answer was difficult. Seeing one technician on a machine in the sample does not prove that the same technician will always work on that machine.

The results make the cost of repeated data easier to see. Changing a machine's site touched one row in the normalized design and 4,000 rows in the report. The checks also showed that all 200,000 rows could be reconstructed and that both dashboard queries returned the same answers.

I got help from Codex with the SQL and Python scripts, running the benchmarks and explaining the results. I still need to add my first FD list and the neighbour-gate feedback. One question I want to ask my pod or instructor is how to decide whether an FD is a real business rule when there is only a small sample to work with.
