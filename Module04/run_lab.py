"""Run Module 4 and save actual evidence. Existing edge.db requires --reset.

--reset rebuilds ONLY this module's edge.db. Do not use it for valuable data.
All learning experiments are run by this script; pod discussion is human work.
"""
import argparse
import platform
import sqlite3
import stat
import subprocess
import sys
import tempfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from ingest import ingest

HERE = Path(__file__).resolve().parent
DB = HERE / "edge.db"
EVIDENCE = HERE / "evidence"


def connect():
    conn = sqlite3.connect(DB.resolve().as_uri() + "?mode=rw", uri=True)
    conn.execute("PRAGMA foreign_keys = ON")
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    return conn


def header(title):
    return [title, "Agent-run experiment; student reproduction/pod discussion is separate.",
            "Measured UTC: " + datetime.now(timezone.utc).isoformat(),
            f"Python {sys.version.split()[0]}; Python SQLite {sqlite3.sqlite_version}",
            f"Platform: {platform.system()} {platform.machine()}", ""]


def save(filename, lines):
    (EVIDENCE / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")


def sql(conn, log, statement, error=None):
    log.append(statement)
    try:
        cursor = conn.execute(statement)
    except sqlite3.Error as exc:
        log.append(f"{type(exc).__name__}: {exc}")
        if error is None or error not in str(exc):
            raise
        log.append("Expected rejection observed.\n")
        return
    if error is not None:
        raise AssertionError("Expected rejection did not occur: " + statement)
    if cursor.description:
        log.append(" | ".join(col[0] for col in cursor.description))
        log.extend(repr(row) for row in cursor.fetchall())
    else:
        log.append("Accepted.")
    log.append("")


def acceptance():
    log = header("Task A: unconstrained acceptance and guarded rejection")
    with closing(sqlite3.connect(":memory:")) as conn:
        sql(conn, log, "CREATE TABLE t(sensor_id INTEGER, metric TEXT, value REAL);")
        sql(conn, log, "INSERT INTO t VALUES (1,'temp_c',9000), "
                      "(1,'temp_c','hot'), (2,'bogus',-500);")
        sql(conn, log, "SELECT *, typeof(value) AS stored_type FROM t;")
        sql(conn, log, "CREATE TABLE guarded(sensor_id INTEGER PRIMARY KEY, "
                      "metric TEXT NOT NULL CHECK(metric IN ('temp_c','vib_rms','spindle_load')), "
                      "value REAL NOT NULL CHECK(value BETWEEN -273.15 AND 5000)) STRICT;")
        for statement, expected, layer in [
            ("INSERT INTO guarded VALUES (1,'temp_c',9000);", "CHECK constraint", "domain"),
            ("INSERT INTO guarded VALUES (1,'temp_c','hot');", "cannot store TEXT", "domain/type"),
            ("INSERT INTO guarded VALUES (2,'bogus',-500);", "CHECK constraint", "domain/metric"),
            ("INSERT INTO guarded VALUES (2,'temp_c',-500);", "CHECK constraint", "domain/range"),
            ("INSERT INTO guarded VALUES (2,NULL,20);", "NOT NULL constraint", "entity/completeness"),
            ("INSERT INTO guarded VALUES (2,'temp_c',NULL);", "NOT NULL constraint", "entity/completeness"),
        ]:
            log.append("Integrity layer: " + layer)
            sql(conn, log, statement, expected)
        sql(conn, log, "INSERT INTO guarded VALUES (1,'temp_c',41.5);")
        log.append("Integrity layer: entity/identity")
        sql(conn, log, "INSERT INTO guarded VALUES (1,'vib_rms',1.4);", "UNIQUE constraint")
        sql(conn, log, "INSERT INTO guarded VALUES (3,'temp_c','41.5');")
        sql(conn, log, "INSERT INTO guarded VALUES (4,'temp_c',120);")
        log.append("120 could be wrong for a particular machine but passes this broad rule.")
        sql(conn, log, "INSERT INTO guarded VALUES (NULL,'temp_c',42);")
        log.append("INTEGER PRIMARY KEY with NULL auto-allocates an ID in SQLite.")
        sql(conn, log, "SELECT *, typeof(value) AS stored_type FROM guarded;")
        sql(conn, log, "CREATE TABLE nullable_check(value REAL CHECK(value BETWEEN -273.15 AND 5000)) STRICT;")
        sql(conn, log, "INSERT INTO nullable_check VALUES (NULL);")
        sql(conn, log, "SELECT value, value BETWEEN -273.15 AND 5000 AS check_result FROM nullable_check;")
        sql(conn, log, "CREATE TABLE nullable_unique(machine TEXT, metric TEXT, UNIQUE(machine,metric)) STRICT;")
        sql(conn, log, "INSERT INTO nullable_unique VALUES ('cnc-01',NULL), ('cnc-01',NULL);")
        sql(conn, log, "SELECT COUNT(*) AS accepted_null_pairs FROM nullable_unique;")
        log.append("The main sensor table avoids this UNIQUE+NULL gap using NOT NULL.")
    save("acceptance.txt", log)


def constraints():
    log = header("Task 1: constraints and generated column")
    with closing(connect()) as conn, conn:
        sql(conn, log, "PRAGMA foreign_keys;")
        sql(conn, log, "INSERT INTO sensor VALUES "
                      "(1,'cnc-01','temp_c','degC'), (2,'cnc-01','vib_rms','mm/s');")
        sql(conn, log, "INSERT INTO reading(sensor_id,ts,value,interval_s) "
                      "VALUES (1,'2026-03-01 08:00:00',41.5,1);")
        cases = [
            ("INSERT INTO reading(sensor_id,ts,value,interval_s) VALUES (1,'2026-03-01 08:00:01',9000,1);", "CHECK constraint", "domain/range"),
            ("INSERT INTO reading(sensor_id,ts,value,interval_s) VALUES (1,'2026-03-01 08:00:02','hot',1);", "cannot store TEXT", "domain/type"),
            ("INSERT INTO reading(sensor_id,ts,value,interval_s) VALUES (99,'2026-03-01 08:00:03',40,1);", "FOREIGN KEY constraint", "referential"),
            ("INSERT INTO sensor VALUES (3,'cnc-01','temp_c','degC');", "UNIQUE constraint", "entity/uniqueness"),
            ("INSERT INTO sensor VALUES (1,'cnc-02','temp_c','degC');", "UNIQUE constraint", "entity/primary key"),
            ("INSERT INTO reading(sensor_id,ts,value,interval_s) VALUES (1,NULL,40,1);", "NOT NULL constraint", "entity/completeness"),
            ("INSERT INTO reading(sensor_id,ts,value,interval_s) VALUES (1,'2026-03-01 08:00:04',40,0);", "CHECK constraint", "domain/interval"),
            ("INSERT INTO sensor VALUES (3,'cnc-03','bogus','?');", "CHECK constraint", "domain/metric"),
        ]
        for statement, error, layer in cases:
            log.append("Integrity layer: " + layer)
            sql(conn, log, statement, error)
        sql(conn, log, "SELECT reading_id,sensor_id,ts,value,interval_s,energy_j FROM reading;")
        assert conn.execute("SELECT energy_j FROM reading").fetchone()[0] == 41.5
        sql(conn, log, "INSERT INTO reading(sensor_id,ts,value,interval_s,energy_j) "
                      "VALUES (1,'2026-03-01 08:00:05',40,1,999);", "cannot INSERT into generated column")
        log.append("Generated arithmetic = 41.5 * 1 = 41.5. Temperature * time is not energy;")
        log.append("the supplied energy_j label is physically misleading for these metrics.")
    save("constraints.txt", log)


def upsert_demo():
    log = header("Task 2: UPSERT and CSV double-run proof")
    with closing(connect()) as conn, conn:
        sql(conn, log, "CREATE UNIQUE INDEX ux_reading_sensor_ts ON reading(sensor_id,ts);")
        sql(conn, log, "INSERT INTO reading(sensor_id,ts,value,interval_s) "
                      "VALUES (1,'2026-03-01 08:00:00',41.7,1) "
                      "ON CONFLICT(sensor_id,ts) DO UPDATE SET value=excluded.value;")
        sql(conn, log, "SELECT sensor_id,ts,value,interval_s FROM reading;")
        assert conn.execute("SELECT COUNT(*) FROM reading").fetchone()[0] == 1
    for i in (1, 2):
        log.append(f"CSV run {i}: uv run python Module04/ingest.py")
        result = subprocess.run([sys.executable, str(HERE / "ingest.py")],
                                capture_output=True, text=True, check=True)
        log.append(result.stdout)
        with closing(connect()) as conn:
            assert conn.execute("SELECT COUNT(*) FROM reading").fetchone()[0] == 4
    with closing(connect()) as conn:
        sql(conn, log, "SELECT sensor_id,ts,value,interval_s,energy_j FROM reading ORDER BY sensor_id,ts;")
        sql(conn, log, "SELECT sensor_id,ts,COUNT(*) AS copies FROM reading "
                      "GROUP BY sensor_id,ts HAVING COUNT(*) > 1;")
        log.append("No duplicate keys returned. Counts: before=1, after first=4, after second=4.")
    with tempfile.TemporaryDirectory(prefix="module04-rejected-csv-") as folder:
        bad = Path(folder) / "invalid.csv"
        bad.write_text("sensor_id,ts,value,interval_s\n"
                       "1,2026-03-02 12:00:00,45,1\n99,2026-03-02 12:00:01,45,1\n")
        try:
            ingest(DB, bad)
        except sqlite3.IntegrityError as exc:
            log.append("Bad CSV test (valid row then nonexistent sensor 99): " + str(exc))
        else:
            raise AssertionError("CSV foreign-key violation was accepted")
        with closing(connect()) as conn:
            count = conn.execute("SELECT COUNT(*) FROM reading").fetchone()[0]
            assert count == 4
            log.append(f"Count after rejected CSV: {count}; whole file transaction rolled back.")
    log.append("Triggers are installed AFTER this experiment to isolate reading-row idempotence.")
    log.append("The supplied UPSERT updates only value; it does not correct interval_s.")
    save("upsert.txt", log)


def trigger_demo():
    log = header("Task 3: alarm, audit, and counterexamples")
    with closing(connect()) as conn:
        conn.executescript((HERE / "triggers.sql").read_text())
        with conn:
            sql(conn, log, "INSERT INTO reading(sensor_id,ts,value,interval_s) "
                          "VALUES (2,'2026-03-01 09:00:00',2.7,1);")
            # Target only the new demonstration row; preserve the CSV fixture.
            sql(conn, log, "UPDATE reading SET value=1.4 WHERE sensor_id=2 AND ts='2026-03-01 09:00:00';")
            sql(conn, log, "SELECT * FROM alarm;")
            sql(conn, log, "SELECT * FROM audit;")
            assert conn.execute("SELECT COUNT(*) FROM alarm").fetchone()[0] == 1
            assert conn.execute("SELECT old_value,new_value FROM audit").fetchall() == [(2.7, 1.4)]
            log.append("Counterexample 1: unchanged value still creates an audit row.")
            sql(conn, log, "UPDATE reading SET value=value WHERE sensor_id=2 AND ts='2026-03-01 09:00:00';")
            sql(conn, log, "SELECT * FROM audit;")
            assert conn.execute("SELECT COUNT(*) FROM audit").fetchone()[0] == 2
            log.append("Counterexample 2: UPSERT corrects a low vibration upward; INSERT alarm does not fire.")
            sql(conn, log, "INSERT INTO reading(sensor_id,ts,value,interval_s) "
                          "VALUES (2,'2026-03-01 10:01:00',2.8,1) "
                          "ON CONFLICT(sensor_id,ts) DO UPDATE SET value=excluded.value;")
            sql(conn, log, "SELECT * FROM alarm;")
            sql(conn, log, "SELECT * FROM audit;")
            assert conn.execute("SELECT COUNT(*) FROM alarm").fetchone()[0] == 1
            assert conn.execute("SELECT COUNT(*) FROM audit").fetchone()[0] == 3
            log.append("Counterexample 3: the audit table is writable. Mutation rolled back after proving it.")
            conn.execute("SAVEPOINT audit_probe")
            sql(conn, log, "UPDATE audit SET new_value=999 WHERE audit_id=1;")
            sql(conn, log, "SELECT audit_id,new_value FROM audit WHERE audit_id=1;")
            sql(conn, log, "ROLLBACK TO audit_probe;")
            conn.execute("RELEASE audit_probe")
            assert conn.execute("SELECT new_value FROM audit WHERE audit_id=1").fetchone()[0] == 1.4
    save("triggers.txt", log)


def cli(log, args, sql_text, expected_error=False):
    # Arguments are passed directly to the process; no shell interpolation.
    log.append("sqlite3 " + " ".join(args) + " " + repr(sql_text))
    result = subprocess.run(["sqlite3", *args, sql_text], capture_output=True, text=True)
    log.append("Exit status: " + str(result.returncode))
    log.append(result.stdout.rstrip())
    if result.stderr:
        log.append(result.stderr.rstrip())
    if expected_error:
        assert result.returncode != 0 and "readonly" in result.stderr.lower(), result
    else:
        assert result.returncode == 0, result.stderr
    log.append("")


def access_control():
    log = header("Task 4: view, file permissions, and read-only connections")
    log.append("CLI SQLite: " + subprocess.check_output(["sqlite3", "--version"], text=True).strip())
    with closing(connect()) as conn:
        view_sql = (HERE / "machine_health.sql").read_text()
        conn.executescript(view_sql)
        log.append(view_sql)
        sql(conn, log, "SELECT * FROM machine_health ORDER BY machine_id,metric;")
    original_mode = stat.S_IMODE(DB.stat().st_mode)
    ro_uri = DB.resolve().as_uri() + "?mode=ro"
    try:
        DB.chmod(0o444)
        log.append("chmod 444 Module04/edge.db")
        log.append("Observed file mode: " + oct(stat.S_IMODE(DB.stat().st_mode)))
        cli(log, [str(DB)], "SELECT COUNT(*) FROM reading;")
        cli(log, [str(DB)], "DELETE FROM reading;", expected_error=True)
        cli(log, [ro_uri], "SELECT COUNT(*) FROM reading;")
        cli(log, [ro_uri], "DELETE FROM reading;", expected_error=True)
    finally:
        DB.chmod(original_mode)
        log.append("Restore original write permissions (normally chmod 644 Module04/edge.db)")
        log.append("Observed file mode: " + oct(stat.S_IMODE(DB.stat().st_mode)))
    log.append("Now the FILE is writable; mode=ro alone still refuses a DELETE.")
    cli(log, [ro_uri], "DELETE FROM reading;", expected_error=True)
    log.append("A read-only reader can STILL read the base table: a view is not an access boundary.")
    cli(log, [ro_uri], "SELECT sensor_id,ts,value FROM reading LIMIT 1;")
    cli(log, [str(DB)], "PRAGMA query_only=ON; DELETE FROM reading;", expected_error=True)
    with closing(connect()) as conn:
        assert conn.execute("SELECT COUNT(*) FROM reading").fetchone()[0] == 5
    save("access-control.txt", log)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    if DB.exists() and not args.reset:
        raise SystemExit("edge.db exists. Use --reset only to rebuild this lab and erase its data.")
    if DB.exists() and stat.S_IMODE(DB.stat().st_mode) & 0o200 == 0:
        raise SystemExit("Restore owner write permission before rebuilding this lab.")
    EVIDENCE.mkdir(exist_ok=True)
    with closing(sqlite3.connect(DB)) as conn:
        conn.executescript((HERE / "setup.sql").read_text())
    acceptance()
    constraints()
    upsert_demo()
    trigger_demo()
    access_control()
    benchmark = subprocess.run([sys.executable, str(HERE / "bench.py")],
                               capture_output=True, text=True, check=True, timeout=60)
    (EVIDENCE / "trigger-cost.txt").write_text(benchmark.stdout)
    variant = subprocess.run([sys.executable, str(HERE / "trigger_variant.py")],
                             capture_output=True, text=True, check=True, timeout=30)
    (EVIDENCE / "trigger-variant.txt").write_text(variant.stdout)
    with closing(connect()) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conn.execute("SELECT COUNT(*) FROM reading").fetchone()[0] == 5
    print("Completed the acceptance experiment and technical Tasks 1-5.")
    print("Actual output saved in Module04/evidence/.")
    print("edge.db: 5 readings; integrity_check=ok; no foreign-key violations.")
    print("Pod study/sharing and the student's personal reflection remain for the student.")


if __name__ == "__main__":
    main()
