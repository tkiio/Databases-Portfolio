-- Rebuild the Module 4 lab (this resets its tables and their data).
PRAGMA foreign_keys = ON;
DROP VIEW IF EXISTS machine_health;
DROP TABLE IF EXISTS audit;
DROP TABLE IF EXISTS alarm;
DROP TABLE IF EXISTS reading;
DROP TABLE IF EXISTS sensor;

CREATE TABLE sensor (
    sensor_id  INTEGER PRIMARY KEY,
    machine_id TEXT NOT NULL,
    metric     TEXT NOT NULL CHECK (metric IN ('temp_c', 'vib_rms', 'spindle_load')),
    unit       TEXT NOT NULL,
    UNIQUE (machine_id, metric)
) STRICT;

CREATE TABLE reading (
    reading_id INTEGER PRIMARY KEY,
    sensor_id  INTEGER NOT NULL REFERENCES sensor(sensor_id),
    ts         TEXT NOT NULL,
    value      REAL NOT NULL,
    interval_s INTEGER NOT NULL CHECK (interval_s > 0),
    -- Preserved from the assignment. This is energy ONLY if value is watts;
    -- temperature * seconds and vibration * seconds are not joules.
    energy_j   REAL GENERATED ALWAYS AS (value * interval_s) VIRTUAL,
    CHECK (value >= -273.15 AND value <= 5000)
) STRICT;
