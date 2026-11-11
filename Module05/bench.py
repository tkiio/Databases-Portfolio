"""Measure warm reads, duplicated updates and storage in the Module 5 lab.

Run after setup/normalization/report creation, or use run_lab.py for all rounds.
The experiment resets its report index, briefly changes one site's rows and
then restores them. It creates a separate wider report for the optional trial.
"""
import json
import platform
import sqlite3
import statistics
import subprocess
import sys
import time
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB = HERE / "normalize.db"
EVIDENCE = HERE / "evidence"
REPEATS = 5
NORMALIZED = (HERE / "dashboard-normalized.sql").read_text()
REPORT = (HERE / "dashboard-report.sql").read_text()


def plan(conn, query):
    return [row[3] for row in conn.execute("EXPLAIN QUERY PLAN " + query)]


def compare(conn, left, right):
    # Warm both sides once, consume the results, then alternate measured order.
    expected = sorted(conn.execute(left).fetchall())
    assert sorted(conn.execute(right).fetchall()) == expected
    times = {"normalized": [], "report": []}
    for repeat in range(REPEATS):
        order = (("normalized", left), ("report", right))
        if repeat % 2:
            order = tuple(reversed(order))
        for name, query in order:
            start = time.perf_counter()
            rows = conn.execute(query).fetchall()
            elapsed_ms = (time.perf_counter() - start) * 1000
            assert sorted(rows) == expected
            times[name].append(elapsed_ms)
    return {"runs_ms": times,
            "median_ms": {key: statistics.median(value) for key, value in times.items()},
            "plans": {"normalized": plan(conn, left), "report": plan(conn, right)},
            "result_groups": len(expected),
            "total_cost": sum(row[-1] for row in expected)}


def storage(conn):
    result = {}
    for design, tables in {"normalized": ("job", "job_part", "part", "machine"),
                           "report": ("report_jobpart",)}.items():
        names = list(tables)
        placeholders = ",".join("?" for _ in tables)
        indexes = [row[0] for row in conn.execute(
            f"SELECT name FROM sqlite_schema WHERE type='index' AND tbl_name IN ({placeholders})", tables)]
        def total(objects):
            marks = ",".join("?" for _ in objects)
            return conn.execute(f"SELECT COALESCE(SUM(pgsize),0) FROM dbstat WHERE name IN ({marks})", objects).fetchone()[0]
        result[design] = {"table_bytes": total(names),
                          "table_and_index_bytes": total(names + indexes),
                          "indexes": indexes}
    return result


def update_benchmark(conn):
    result = {}
    machine_id = "cnc-02"
    original_site = conn.execute("SELECT site FROM machine WHERE machine_id=?", (machine_id,)).fetchone()[0]
    result["original_site"] = original_site
    result["new_site"] = "Bielefeld"
    for name, table in (("normalized", "machine"), ("report", "report_jobpart")):
        query = f"UPDATE {table} SET site=? WHERE machine_id=?"
        times = []
        touched = []
        for repeat in range(REPEATS + 1):
            conn.execute(query, (original_site, machine_id))
            conn.commit()  # reset outside timing
            start = time.perf_counter()
            cursor = conn.execute(query, ("Bielefeld", machine_id))
            conn.commit()  # include write durability in the measurement
            elapsed_ms = (time.perf_counter() - start) * 1000
            if repeat:
                times.append(elapsed_ms)
                touched.append(cursor.rowcount)
        result[name] = {"sql": query, "runs_ms": times,
                        "median_ms": statistics.median(times),
                        "rows_touched": touched[0]}
        assert len(set(touched)) == 1
        if name == "normalized":
            stale = conn.execute("SELECT COUNT(*) FROM report_jobpart AS r JOIN machine AS m "
                                 "USING(machine_id) WHERE r.site != m.site").fetchone()[0]
            assert stale == 4000
            result["stale_report_rows_before_sync"] = stale
    assert result["normalized"]["rows_touched"] == 1
    assert result["report"]["rows_touched"] == 4000
    assert conn.execute("SELECT COUNT(*) FROM report_jobpart AS r JOIN machine AS m "
                        "USING(machine_id) WHERE r.site != m.site").fetchone()[0] == 0
    # Restore both labels so all later comparisons use the original facts.
    for table in ("machine", "report_jobpart"):
        conn.execute(f"UPDATE {table} SET site=? WHERE machine_id=?", (original_site, machine_id))
    conn.commit()
    return result


def append_comparison(log, label, result):
    log.extend(["", label, "Both result sets match exactly.",
                f"Groups: {result['result_groups']}; total cost: {result['total_cost']}"])
    for name in ("normalized", "report"):
        log.append(name + " runs_ms: " + ", ".join(f"{t:.3f}" for t in result["runs_ms"][name]))
        log.append(f"{name} median_ms: {result['median_ms'][name]:.3f}")
        log.append(name + " EXPLAIN QUERY PLAN:")
        log.extend("  " + line for line in result["plans"][name])


def recommendations(result):
    indexed = result["indexed"]["median_ms"]
    unindexed = result["unindexed"]["median_ms"]
    n = unindexed["normalized"]
    d = unindexed["report"]
    winner = "reporting copy" if d < n else "normalized query"
    storage_result = result["storage_without_index"]
    if storage_result:
        extra = storage_result["report"]["table_and_index_bytes"] / 1024
        cost = f"the report adds {extra:.1f} KiB including its remaining indexes"
    else:
        cost = "the report repeats the site, technician and price on many rows; dbstat was unavailable"
    sentences = [
        f"For this dataset, I recommend the {winner} for the dashboard, based on warm medians of {n:.3f} ms for 3NF and {d:.3f} ms for the reporting copy without its machine index.",
        "I would keep the transactional tables in 3NF so that each machine, part and job fact has one main place to change.",
        f"The report's machine index is not an automatic improvement: its median was {indexed['report']:.3f} ms with the index and {d:.3f} ms without it, and the saved plans show the access paths.",
        f"Changing one site touched 1 normalized row but 4,000 report rows, and {cost} if both designs are kept.",
        "If a reporting copy is used, I would rebuild it from the normalized tables in one transaction every 30 seconds, publish a last-refreshed timestamp and let readers see either the previous complete version or the new one.",
        "This targets roughly 30-second freshness, but rebuilding time, scheduling delays and failures can add lag, so the timestamp must make that visible and refresh failures must be reported.",
        "If the dashboard needs immediate correctness, I would read 3NF directly or maintain every affected insert, update and delete in the same transaction, rather than relying on a site-only trigger.",
        "I would remeasure with the real workload before extending this decision, because this fixed March query and 200,000-row cache-friendly dataset do not establish production performance.",
    ]
    (HERE / "recommendation.md").write_text("# My recommendation to Yasmin Kaya\n\n" + " ".join(sentences) +
        "\n\n[My benchmark table](benchmark-results.md) · [Exact timings and plans](evidence/benchmark.txt)\n", encoding="utf-8")


def write_table(result):
    def size(state, design, key):
        return f"{state[design][key] / 1024:.1f}" if state else "Unavailable"
    lines = ["# My benchmark results", "",
        "Wall-clock medians from five warm runs per query, on one Python SQLite connection. All result rows were fetched and compared. These are measured laptop results, not the production story's 40 seconds.", "",
        "| Design | Dashboard median (ms) | Site-update median (ms) | Rows updated | Table storage (KiB) | Tables + indexes (KiB) | Redundancy |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |"]
    for label, state, name, query_time, redundancy in [
        ("Normalized (3NF)", result["storage_with_index"], "normalized", result["indexed"]["median_ms"]["normalized"], "Facts stored once in their own tables"),
        ("Report, with machine index", result["storage_with_index"], "report", result["indexed"]["median_ms"]["report"], "Site, technician and price repeated"),
        ("Report, without machine index", result["storage_without_index"], "report", result["unindexed"]["median_ms"]["report"], "Same repeated facts"),
    ]:
        write = result["writes"][name]
        write_time = "Not measured" if label == "Report, without machine index" else f"{write['median_ms']:.3f}"
        lines.append(f"| {label} | {query_time:.3f} | {write_time} | {write['rows_touched']:,} | "
                     f"{size(state,name,'table_bytes')} | {size(state,name,'table_and_index_bytes')} | {redundancy} |")
    lines.extend(["", "The site updates were measured with the report index present. No separate no-index write timing is claimed.", "",
        f"The paired no-index rerun measured the normalized query again at **{result['unindexed']['median_ms']['normalized']:.3f} ms**. Compare both timings within the same paired experiment. The normalized time also changed between phases, so the entire report-time difference cannot be assigned to the index alone.", "",
        "Table-only storage matches the handout's dbstat query. The additional column counts associated indexes, including primary-key indexes. The flat source and optional wider report are excluded from these design totals. Keeping a report alongside 3NF adds its storage; it does not replace the source tables.", "",
        "The dataset has 200,000 lines, 20,000 jobs, 50 machines and 10 parts. Both main queries return 350 groups and a total of 722,610.0. The WHERE clause is a fixed lower date bound, not a rolling 90-day window.", "",
        "## Optional wider comparison", "",
        "The wider test uses six normalized tables (five joins) and a separate reporting copy with no machine index, so it leaves the main experiment intact.", "",
        f"Normalized median: **{result['wide']['median_ms']['normalized']:.3f} ms**. Report median: **{result['wide']['median_ms']['report']:.3f} ms**. Both return 3,500 groups totalling 722,610.0.", "",
        "[All runs, plans and storage](evidence/benchmark.txt) · [Machine-readable measurements](evidence/benchmark.json) · [My recommendation](recommendation.md)"])
    (HERE / "benchmark-results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    if not DB.exists():
        raise SystemExit("normalize.db is missing. Run: uv run python Module05/run_lab.py")
    EVIDENCE.mkdir(exist_ok=True)
    with closing(sqlite3.connect(DB.resolve().as_uri() + "?mode=rw", uri=True, cached_statements=0)) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        # Fix the same durability settings throughout, before transactions.
        assert conn.execute("PRAGMA journal_mode=DELETE").fetchone()[0] == "delete"
        conn.execute("PRAGMA synchronous=FULL")
        assert conn.execute("PRAGMA synchronous").fetchone()[0] == 2
        conn.execute("CREATE INDEX IF NOT EXISTS ix_report_machine ON report_jobpart(machine_id)")
        conn.commit()
        log = ["Module 5: query, update and storage measurements",
               "Measured UTC: " + datetime.now(timezone.utc).isoformat(),
               f"Python {sys.version.split()[0]}; Python SQLite {sqlite3.sqlite_version}",
               "CLI SQLite: " + subprocess.check_output(["sqlite3", "--version"], text=True).strip(),
               f"Platform: {platform.system()} {platform.machine()}",
               f"Warm-up: 1 per query; measured runs: {REPEATS}; alternating order; fetchall inside timer.",
               "No ANALYZE; cached_statements=0 to prepare fresh plans after index changes.",
               "journal_mode=DELETE, synchronous=FULL (set and checked). No other machine workload controlled."]
        result = {"python": sys.version.split()[0], "sqlite": sqlite3.sqlite_version,
                  "measured_utc": datetime.now(timezone.utc).isoformat()}
        result["indexed"] = compare(conn, NORMALIZED, REPORT)
        assert result["indexed"]["result_groups"] == 350
        assert result["indexed"]["total_cost"] == 722610.0
        append_comparison(log, "Round 4: report machine index present", result["indexed"])
        try:
            result["storage_with_index"] = storage(conn)
        except sqlite3.OperationalError as exc:
            result["storage_with_index"] = None
            log.append("dbstat unavailable: " + str(exc))
        result["writes"] = update_benchmark(conn)
        log.extend(["", "Round 5: site updates, one warm-up then five timed update+commit runs",
                    json.dumps(result["writes"], indent=2),
                    "After the normalized change alone, 4,000 report rows were stale.",
                    "Updating the copy fixed the mismatch. Both sites were then restored."])
        conn.execute("DROP INDEX ix_report_machine")
        conn.commit()
        result["unindexed"] = compare(conn, NORMALIZED, REPORT)
        append_comparison(log, "Round 5: report machine index removed", result["unindexed"])
        try:
            result["storage_without_index"] = storage(conn)
        except sqlite3.OperationalError:
            result["storage_without_index"] = None
        log.extend(["", "Storage: bytes per design (flat source and wider experiment excluded)",
                    "With report index: " + json.dumps(result["storage_with_index"], indent=2),
                    "Without report index: " + json.dumps(result["storage_without_index"], indent=2)])
        conn.executescript((HERE / "dimensions.sql").read_text())
        wide_normalized = """SELECT m.machine_id,m.site,sd.region,j.technician,v.vendor,SUM(p.part_price) AS cost
FROM job AS j JOIN machine AS m ON m.machine_id=j.machine_id
JOIN site_dim AS sd ON sd.site=m.site JOIN job_part AS jp ON jp.job_id=j.job_id
JOIN part AS p ON p.part_no=jp.part_no JOIN vendor AS v ON v.part_no=p.part_no
WHERE j.done_on >= date('2026-03-01')
GROUP BY m.machine_id,m.site,sd.region,j.technician,v.vendor"""
        wide_report = """SELECT machine_id,site,region,technician,vendor,SUM(part_price) AS cost
FROM report_jobpart_wide WHERE done_on >= date('2026-03-01')
GROUP BY machine_id,site,region,technician,vendor"""
        result["wide"] = compare(conn, wide_normalized, wide_report)
        result["wide"]["sql"] = {"normalized": wide_normalized, "report": wide_report}
        assert result["wide"]["result_groups"] == 3500 and result["wide"]["total_cost"] == 722610.0
        append_comparison(log, "Optional: two additional dimensions, no report index", result["wide"])
        log.extend(["Wider normalized SQL:", wide_normalized, "Wider report SQL:", wide_report])
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conn.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
    (EVIDENCE / "benchmark.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    (EVIDENCE / "benchmark.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    write_table(result)
    recommendations(result)
    print("Benchmarks saved: indexed/unindexed/wider reads, site updates, storage, plans and recommendation.")


if __name__ == "__main__":
    main()
