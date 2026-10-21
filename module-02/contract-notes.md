# Repaired schema contract

- [`contract.py`](contract.py) contains the Pydantic data models and SQLAlchemy table definitions.
- [`contract-ddl.sql`](contract-ddl.sql) is the emitted SQLite DDL.

## Which layer enforces what?

Pydantic checks incoming values in the application: IDs must be positive, required strings cannot be empty, dates must parse as dates, prices must be non-negative decimals, and machine serial numbers must begin with `SN-`. These checks give a useful validation error before an insert is attempted.

The database enforces rules that must remain true across every program that writes to it: primary keys identify rows, `UNIQUE` prevents duplicate machine serial numbers, `NOT NULL` requires values, foreign keys prevent orphan jobs and job-part links, and the composite key prevents listing the same part twice on one job. These rules still apply if a different application writes to the database.

SQLite needs `PRAGMA foreign_keys = ON` for every connection to enforce foreign keys. Pydantic alone cannot verify that a referenced machine, technician, or part actually exists; the database constraint does that.

`part_no` is used as the part's natural key and is now declared as its primary key. `machine_id` and `technician_id` are surrogate keys; the machine serial is also constrained to be unique.
