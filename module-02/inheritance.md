# EER inheritance stretcher: machine types

The common machine properties stay in a supertype `Machine`; the two subtypes add their own attributes. The examples assume a CNC mill has `spindle_count` and an injection molder has `clamp_force_kn`, as representative type-specific properties.

## Option 1: one table with a discriminator

```sql
CREATE TABLE machine (
    machine_id INTEGER PRIMARY KEY,
    machine_type TEXT NOT NULL CHECK (machine_type IN ('cnc_mill', 'injection_molder')),
    serial_no TEXT NOT NULL UNIQUE,
    site TEXT NOT NULL,
    spindle_count INTEGER,
    clamp_force_kn NUMERIC,
    CHECK (
        (machine_type = 'cnc_mill' AND spindle_count IS NOT NULL AND clamp_force_kn IS NULL)
        OR
        (machine_type = 'injection_molder' AND clamp_force_kn IS NOT NULL AND spindle_count IS NULL)
    )
);
```

The discriminator and `CHECK` make each row exactly one of the two types. Type-specific columns are nullable for the other subtype.

## Option 2: supertype plus one table per subtype

```sql
CREATE TABLE machine (
    machine_id INTEGER PRIMARY KEY,
    machine_type TEXT NOT NULL CHECK (machine_type IN ('cnc_mill', 'injection_molder')),
    serial_no TEXT NOT NULL UNIQUE,
    site TEXT NOT NULL,
    UNIQUE (machine_id, machine_type)
);

CREATE TABLE cnc_mill (
    machine_id INTEGER PRIMARY KEY,
    machine_type TEXT NOT NULL DEFAULT 'cnc_mill'
        CHECK (machine_type = 'cnc_mill'),
    spindle_count INTEGER NOT NULL,
    FOREIGN KEY (machine_id, machine_type)
        REFERENCES machine(machine_id, machine_type)
);

CREATE TABLE injection_molder (
    machine_id INTEGER PRIMARY KEY,
    machine_type TEXT NOT NULL DEFAULT 'injection_molder'
        CHECK (machine_type = 'injection_molder'),
    clamp_force_kn NUMERIC NOT NULL,
    FOREIGN KEY (machine_id, machine_type)
        REFERENCES machine(machine_id, machine_type)
);
```

The composite foreign keys and fixed type checks enforce disjointness: one parent row cannot have both subtype values. This design still needs an additional check or trigger if every parent machine must have a matching subtype row; foreign keys alone do not enforce that each parent has a child.

## My decision

Suggested rationale to discuss with the pod: for only two stable machine types with distinct required fields, I would choose the supertype plus subtype tables because it avoids irrelevant nullable columns; I would add database enforcement so each machine is in exactly one subtype. Change this sentence if your group prefers the simpler single-table design for the current scale.
