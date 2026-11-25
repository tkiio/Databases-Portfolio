# Reflection 5

My main takeaway from this module is that normalization reduces repeated information, but a reporting copy can make some queries faster. That copy also needs more storage and has to be kept up to date. I want to remember that fewer joins do not automatically mean a query will be faster.

The hardest part for me was naming the functional dependencies and deciding which ones were real domain rules and which were only patterns in the five rows. Drawing the two ER sketches and comparing the FD list with the model's answer was difficult. Seeing one technician on a machine in the sample does not prove that the same technician will always work on that machine.

The results make the cost of repeated data easier to see. Changing a machine's site touched one row in the normalized design and 4,000 rows in the report. The checks also showed that all 200,000 rows could be reconstructed and that both dashboard queries returned the same answers.

Codex helped me with the SQL and benchmarks. The bigger dataset gave me a way to check the FD about technicians because it had several technicians working on the same machine. One question I would bring to the pod is whether we should use the current price of a part or the price paid for that job.
