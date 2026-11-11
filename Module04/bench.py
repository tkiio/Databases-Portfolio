"""Measure 10,000-row file ingests with and without the course alarm trigger.

Temporary databases are removed automatically. Setup is outside the timed
region; executemany AND commit are inside. Each pair uses the same rows and
a fresh empty reading table, with an identical schema and unique index.
"""
import platform
import sqlite3
import statistics
import sys
import tempfile
import time
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROWS = 10_000
REPEATS = 5


def benchmark(value: float, enabled: bool) -> float:
    start_ts = datetime(2026, 3, 2)
    rows = [(2, (start_ts + timedelta(seconds=i)).isoformat(" "), value, 1)
            for i in range(ROWS)]
    with tempfile.TemporaryDirectory(prefix="module04-bench-") as folder:
        with closing(sqlite3.connect(Path(folder) / "bench.db")) as conn:
            assert conn.execute("PRAGMA journal_mode=DELETE").fetchone()[0] == "delete"
            conn.execute("PRAGMA synchronous=FULL")
            assert conn.execute("PRAGMA synchronous").fetchone()[0] == 2
            conn.executescript((HERE / "setup.sql").read_text())
            conn.executescript((HERE / "triggers.sql").read_text())
            conn.execute("DROP TRIGGER trg_reading_audit")  # no UPDATE in this test
            if not enabled:
                conn.execute("DROP TRIGGER trg_vib_alarm")
            conn.execute("CREATE UNIQUE INDEX ux_reading_sensor_ts ON reading(sensor_id, ts)")
            conn.execute("INSERT INTO sensor VALUES (2, 'cnc-01', 'vib_rms', 'mm/s')")
            conn.commit()
            begin = time.perf_counter()
            with conn:
                conn.executemany("INSERT INTO reading(sensor_id, ts, value, interval_s) "
                                 "VALUES (?, ?, ?, ?)", rows)
            elapsed = time.perf_counter() - begin
            assert conn.execute("SELECT COUNT(*) FROM reading").fetchone()[0] == ROWS
            alarms = conn.execute("SELECT COUNT(*) FROM alarm").fetchone()[0]
            assert alarms == (ROWS if enabled and value > 2.0 else 0)
            return elapsed


def main() -> None:
    print("Trigger cost: agent-run experiment on this laptop")
    print("Measured UTC:", datetime.now(timezone.utc).isoformat())
    print("Python:", sys.version.split()[0], "SQLite:", sqlite3.sqlite_version)
    print("Platform:", platform.system(), platform.machine())
    print("Rows per transaction:", ROWS, "measured repetitions:", REPEATS)
    print("Enforced and checked: journal_mode=delete, synchronous=FULL; both cases identical.")
    print("One unrecorded warm-up per case; paired order alternates per repetition.")
    print("Times include INSERT + COMMIT; setup, connection, row building excluded.")
    for value in (1.4, 2.7):
        times = {False: [], True: []}
        for enabled in (False, True):
            benchmark(value, enabled)
        for repeat in range(REPEATS):
            for enabled in ((False, True) if repeat % 2 == 0 else (True, False)):
                times[enabled].append(benchmark(value, enabled))
        print(f"\nVibration {value} mm/s: " + ("alarm fires" if value > 2 else "no alarm"))
        for enabled in (False, True):
            print("With trigger" if enabled else "Without trigger")
            print("  runs_ms:", ", ".join(f"{t * 1000:.3f}" for t in times[enabled]))
            print(f"  median_ms: {statistics.median(times[enabled]) * 1000:.3f}")
        ratio = statistics.median(times[True]) / statistics.median(times[False])
        print(f"  with/without median ratio: {ratio:.3f}x")
        print("  alarm rows with trigger:", ROWS if value > 2 else 0)
    print("\nThese are local measurements, not a universal trigger overhead.")


if __name__ == "__main__":
    main()
