# Task 3: The injection drill

The runnable demonstration is in [`injection_demo.py`](injection_demo.py). I ran it from the portfolio root with:

```bash
python3 Module03/injection_demo.py
```

## Output

```text
normal   : [(1, 'Customer 1')]
apostrophe: crashed with near "Neil": syntax error
apostrophe safe: []
injected : [(1, 'Customer 1'), (2, 'Customer 2'), (3, 'Customer 3')] ...
safe     : []
```

The apostrophe input was `O'Neil`. In the vulnerable function, string interpolation produces malformed SQL and SQLite raises a syntax error. The injection payload was `' OR '1'='1`; concatenating it into the query changes the condition and returns customer rows. With the safe function, both inputs are bound as values, so the apostrophe does not break the SQL and the injection string is just a name to search for.

## Why binding is the fix

Hand-escaping or filtering apostrophes is fragile: the correct escaping depends on SQL dialect, quoting context, data type, and encoding, and a value may appear in a string, numeric, or other context. It is easy to miss a case or alter legitimate input. Bound parameters keep SQL structure separate from values; the database driver handles the value's representation and type, so the input cannot become SQL syntax. Parameters represent values, not table or column identifiers; dynamic identifiers should be selected from an allowlist and quoted according to the database's rules.
