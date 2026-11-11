"""Run the five-row anomaly examples and save their actual output.

All examples use disposable databases. No changes to normalize.db.
"""
import sqlite3
import sys
import tempfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "anomalies.sql"
EXPECTED = {
    "baseline_rows": 5,
    "touched_site_rows": 3,
    "inconsistent_machines": 1,
    "unused_part_placeholder_rows": 1,
    "removed_job1_rows": 2,
    "retained_part2_rows": 0,
    "restored_rows": 5,
}


def statements(text):
    pending = ""
    for line in text.splitlines():
        pending += line + "\n"
        if sqlite3.complete_statement(pending):
            yield pending.strip()
            pending = ""
    if pending.strip() and not all(
        not line.strip() or line.lstrip().startswith("--")
        for line in pending.splitlines()
    ):
        raise ValueError("Unfinished SQL statement")


def single_connection_examples(log):
    with closing(sqlite3.connect(":memory:")) as conn:
        for statement in statements(SOURCE.read_text(encoding="utf-8")):
            log.append(statement)
            cursor = conn.execute(statement)
            if cursor.description:
                names = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                log.append(" | ".join(names))
                log.extend(repr(row) for row in rows)
                if len(names) == 1 and names[0] in EXPECTED:
                    assert rows == [(EXPECTED[names[0]],)], (names, rows)
            else:
                log.append("Accepted.")
            log.append("")


def two_connection_example(log):
    log.extend([
        "Two-session example: a writer lock does not repair duplicated facts.",
        "Both sessions edit separate copies of the same machine's site.",
        "The temporary database uses the default rollback-journal mode.",
    ])
    setup = SOURCE.read_text(encoding="utf-8").split("-- Case 1:")[0]
    with tempfile.TemporaryDirectory(prefix="module05-anomaly-") as folder:
        db = Path(folder) / "two-sessions.db"
        with closing(sqlite3.connect(db)) as a, closing(sqlite3.connect(db)) as b:
            a.executescript(setup)
            b.execute("PRAGMA busy_timeout=100")
            a.execute("BEGIN IMMEDIATE")
            first = "UPDATE flat5 SET site='Bielefeld' WHERE job_id=1 AND part_no='P-0001'"
            second = "UPDATE flat5 SET site='Münster' WHERE job_id=3"
            log.append("A: BEGIN IMMEDIATE;")
            a.execute(first)
            log.append("A: " + first + ";")
            log.append("B tries before A commits: " + second + ";")
            try:
                b.execute(second)
            except sqlite3.OperationalError as exc:
                log.append("B: " + str(exc))
                assert "locked" in str(exc).lower()
                b.rollback()
            else:
                raise AssertionError("Second writer unexpectedly succeeded during A's write")
            a.commit()
            log.append("A: COMMIT;")
            b.execute(second)
            b.commit()
            log.append("B retries after A commits, then COMMIT: accepted.")
            rows = b.execute(
                "SELECT job_id,part_no,site FROM flat5 WHERE machine_id='cnc-01' "
                "ORDER BY job_id,part_no"
            ).fetchall()
            log.append("Result (job_id, part_no, site):")
            log.extend(repr(row) for row in rows)
            assert len({row[2] for row in rows}) == 3, rows
            log.append("Three different sites remain for cnc-01 despite serialized writes.")
            log.append("This is a logical update anomaly, not simultaneous database corruption.")


def main():
    log = [
        "Module 5: update, insert and delete anomalies",
        "Measured UTC: " + datetime.now(timezone.utc).isoformat(),
        f"Python {sys.version.split()[0]}; SQLite {sqlite3.sqlite_version}",
        "Each main example restores the same initial five rows.",
        "",
    ]
    single_connection_examples(log)
    two_connection_example(log)
    output = "\n".join(log) + "\n"
    target = HERE / "evidence" / "anomalies.txt"
    target.parent.mkdir(exist_ok=True)
    target.write_text(output, encoding="utf-8")
    print(output, end="")


if __name__ == "__main__":
    main()
