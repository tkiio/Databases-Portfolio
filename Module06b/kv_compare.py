"""20,000 session sets/gets in shelve and SQLite; three fresh measured runs."""
import dbm
import json
import shelve
import sqlite3
import statistics
import sys
import tempfile
import time
from contextlib import closing
from datetime import datetime,timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
N=20_000
RUNS=3
rows=[(f"session-{i}",f"user-{i%100}:filter=city:{i%4}") for i in range(N)]


def shelf_run(folder):
    path=folder/"sessions"
    with shelve.open(str(path),flag="n") as store:
        start=time.perf_counter()
        for key,value in rows:store[key]=value
        store.sync()  # include a flush, rather than timing assignment alone
        set_s=time.perf_counter()-start
        start=time.perf_counter()
        values=[store[key] for key,_ in rows]
        get_s=time.perf_counter()-start
        assert values==[v for _,v in rows] and len(store)==N
    backend=dbm.whichdb(str(path))
    return set_s,get_s,backend


def sqlite_run(folder):
    with closing(sqlite3.connect(folder/"sessions.db")) as conn:
        conn.execute("CREATE TABLE session(k TEXT NOT NULL PRIMARY KEY,v TEXT NOT NULL)")
        start=time.perf_counter()
        with conn:conn.executemany("INSERT OR REPLACE INTO session(k,v) VALUES (?,?)",rows)
        set_s=time.perf_counter()-start
        start=time.perf_counter()
        values=[conn.execute("SELECT v FROM session WHERE k=?",(key,)).fetchone()[0] for key,_ in rows]
        get_s=time.perf_counter()-start
        assert values==[v for _,v in rows]
        assert conn.execute("SELECT COUNT(*) FROM session").fetchone()[0]==N
        assert conn.execute("SELECT COUNT(*) FROM session WHERE v LIKE '%city:1'").fetchone()[0]==5000
    return set_s,get_s


def trial(engine):
    with tempfile.TemporaryDirectory(prefix="sessions-",dir=HERE) as folder:
        return (shelf_run if engine=="shelve" else sqlite_run)(Path(folder))


def main():
    print("20,000 sets and 20,000 gets per engine; fresh stores; three measured runs.")
    print("One warm-up per engine; measured order alternates; payloads built outside timing.")
    print("shelve set includes sync(); SQLite set includes one transaction commit.")
    print("These flush calls do not establish equal crash-durability guarantees.")
    results={e:{"set_s":[],"get_s":[]} for e in ("shelve","sqlite")}
    backends=set()
    for engine in results:trial(engine)
    for repeat in range(RUNS):
        for engine in (["shelve","sqlite"] if repeat%2==0 else ["sqlite","shelve"]):
            values=trial(engine)
            results[engine]["set_s"].append(values[0])
            results[engine]["get_s"].append(values[1])
            if engine=="shelve":backends.add(values[2])
    for engine,item in results.items():
        item["median_set_s"]=statistics.median(item["set_s"])
        item["median_get_s"]=statistics.median(item["get_s"])
        print(f"{engine:7s} set={item['median_set_s']:.4f}s get={item['median_get_s']:.4f}s")
        print("  set runs:",item["set_s"],"get runs:",item["get_s"])
    print("shelve backend:",sorted(backends))
    print("All stored values and read values matched; SQL city:1 count=5000.")
    print("No timestamps are stored, so this fixture cannot answer a last-week query.")
    result={"measured_utc":datetime.now(timezone.utc).isoformat(),"python":sys.version.split()[0],
            "sqlite":sqlite3.sqlite_version,"shelve_backends":sorted(backends),"n":N,"runs":RUNS,"results":results}
    (HERE/"evidence").mkdir(exist_ok=True)
    (HERE/"evidence/kv-results.json").write_text(json.dumps(result,indent=2)+"\n")


if __name__=="__main__":main()
