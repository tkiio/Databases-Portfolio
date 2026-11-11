PRAGMA foreign_keys = ON;

CREATE TABLE alarm (
    alarm_id  INTEGER PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES sensor(sensor_id),
    ts        TEXT NOT NULL,
    value     REAL NOT NULL,
    reason    TEXT NOT NULL
) STRICT;

CREATE TABLE audit (
    audit_id   INTEGER PRIMARY KEY,
    reading_id INTEGER NOT NULL,
    old_value  REAL,
    new_value  REAL,
    changed_at TEXT NOT NULL DEFAULT (datetime('now'))
) STRICT;

-- Course version: reacts to INSERT only. See integrity-notes.md for the
-- deliberate UPSERT/update counterexample and the audit's limitations.
CREATE TRIGGER trg_vib_alarm
AFTER INSERT ON reading
FOR EACH ROW
WHEN NEW.value > 2.0 AND
     (SELECT metric FROM sensor WHERE sensor_id = NEW.sensor_id) = 'vib_rms'
BEGIN
    INSERT INTO alarm(sensor_id, ts, value, reason)
    VALUES (NEW.sensor_id, NEW.ts, NEW.value, 'vibration over 2.0 mm/s');
END;

CREATE TRIGGER trg_reading_audit
AFTER UPDATE OF value ON reading
FOR EACH ROW
BEGIN
    INSERT INTO audit(reading_id, old_value, new_value)
    VALUES (NEW.reading_id, OLD.value, NEW.value);
END;
