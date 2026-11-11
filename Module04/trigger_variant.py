"""Compare BEFORE/AFTER alarm triggers in separate, disposable databases."""
import platform
import sqlite3


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE sensor(
    sensor_id INTEGER PRIMARY KEY,
    metric TEXT NOT NULL
) STRICT;
INSERT INTO sensor VALUES (2, 'vib_rms');
CREATE TABLE reading(
    reading_id INTEGER PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES sensor(sensor_id),
    ts TEXT NOT NULL,
    value REAL NOT NULL CHECK(value BETWEEN -273.15 AND 5000),
    interval_s INTEGER NOT NULL CHECK(interval_s > 0)
) STRICT;
CREATE TABLE alarm(
    alarm_id INTEGER PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES sensor(sensor_id),
    ts TEXT NOT NULL,
    value REAL NOT NULL,
    reason TEXT NOT NULL
) STRICT;
CREATE TABLE trigger_probe(reading_count INTEGER NOT NULL) STRICT;
"""


def alarm_variant(timing: str) -> None:
    # Only these two fixed timing keywords may be included in the DDL.
    assert timing in {"BEFORE", "AFTER"}
    with sqlite3.connect(":memory:") as conn:
        conn.executescript(SCHEMA)
        trigger = f"""CREATE TRIGGER trg_vib_alarm
{timing} INSERT ON reading
FOR EACH ROW
WHEN NEW.value > 2.0 AND
     (SELECT metric FROM sensor WHERE sensor_id = NEW.sensor_id) = 'vib_rms'
BEGIN
    INSERT INTO alarm(sensor_id, ts, value, reason)
    VALUES (NEW.sensor_id, NEW.ts, NEW.value, 'vibration over 2.0 mm/s');
    INSERT INTO trigger_probe SELECT COUNT(*) FROM reading;
END;"""
        conn.executescript(trigger)
        print(f"\n=== {timing} INSERT ===")
        print(trigger)
        # Explicit reading_id avoids undefined NEW.rowid in a BEFORE INSERT.
        sql = "INSERT INTO reading VALUES (1, 2, '2026-03-01 09:00:00', 2.7, 1)"
        print(sql + ";")
        conn.execute(sql)
        conn.commit()
        alarms = conn.execute(
            "SELECT sensor_id, ts, value, reason FROM alarm"
        ).fetchall()
        probes = conn.execute("SELECT reading_count FROM trigger_probe").fetchall()
        print("alarm rows:", alarms)
        print("reading COUNT(*) observed inside the trigger:", probes)
        assert len(alarms) == 1
        assert probes == [(0 if timing == "BEFORE" else 1,)]

        before = conn.execute(
            "SELECT (SELECT COUNT(*) FROM reading),"
            " (SELECT COUNT(*) FROM alarm), (SELECT COUNT(*) FROM trigger_probe)"
        ).fetchone()
        bad = "INSERT INTO reading VALUES (2, 2, '2026-03-01 09:00:01', 9000, 1)"
        print(bad + ";")
        try:
            conn.execute(bad)
        except sqlite3.IntegrityError as exc:
            print("rejected:", exc)
        else:
            raise AssertionError("Invalid reading unexpectedly accepted")
        after = conn.execute(
            "SELECT (SELECT COUNT(*) FROM reading),"
            " (SELECT COUNT(*) FROM alarm), (SELECT COUNT(*) FROM trigger_probe)"
        ).fetchone()
        print("counts (reading, alarm, probe) before/after rejected insert:", before, after)
        assert before == after


def rejection_variant(timing: str) -> None:
    assert timing in {"BEFORE", "AFTER"}
    with sqlite3.connect(":memory:") as conn:
        conn.executescript(SCHEMA)
        conn.executescript(f"""
CREATE TRIGGER reject_high_vibration {timing} INSERT ON reading
WHEN NEW.value > 2.0
BEGIN
    SELECT RAISE(ABORT, 'vibration exceeds policy');
END;
""")
        try:
            conn.execute("INSERT INTO reading VALUES (1, 2, '2026-03-01 09:00:00', 2.7, 1)")
        except sqlite3.IntegrityError as exc:
            print(f"{timing} RAISE(ABORT): {exc}")
        else:
            raise AssertionError("RAISE trigger did not reject the insert")
        count = conn.execute("SELECT COUNT(*) FROM reading").fetchone()[0]
        print("persisted reading rows:", count)
        assert count == 0


if __name__ == "__main__":
    print("Python:", platform.python_version())
    print("SQLite (Python library):", sqlite3.sqlite_version)
    print("Isolated in-memory databases; no changes to edge.db.")
    for timing in ("BEFORE", "AFTER"):
        alarm_variant(timing)
    print("\n=== RAISE(ABORT) can reject at either timing ===")
    for timing in ("BEFORE", "AFTER"):
        rejection_variant(timing)
