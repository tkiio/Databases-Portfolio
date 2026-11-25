"""Store vendor metadata in SQLite and compare two JSON query plans."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "evidence"
OUT.mkdir(exist_ok=True)


def main():
    with closing(sqlite3.connect(HERE / "polyglot.db", cached_statements=0)) as con:
        con.executescript("""
        DROP TABLE IF EXISTS device;
        CREATE TABLE device(
            device_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            meta TEXT NOT NULL CHECK(json_valid(meta))
        ) STRICT;
        """)
        rows = [
            ("cnc-01", '{"vendor":"Siemens","firmware":"4.2","calibrated":"2026-01-10"}'),
            ("cnc-02", '{"vendor":"Fanuc","firmware":"3.9"}'),
            ("molder-07", '{"vendor":"Arburg","firmware":"8.1","calibrated":"2025-11-02","nozzle_mm":2.5}'),
        ]
        for i in range(4,1001):
            rows.append((f"device-{i:04d}", json.dumps({
                "vendor": ("Siemens","Fanuc","Arburg")[i % 3],
                "firmware": f"{i % 5}.{i % 10}",
            })))
        with con:
            con.executemany("INSERT INTO device(name,meta) VALUES (?,?)",rows)
        print("SQLite:",sqlite3.sqlite_version)
        print("Device rows:",con.execute("SELECT COUNT(*) FROM device").fetchone()[0])
        for title,query in [
            ("A path behaves like a column", "SELECT name,json_extract(meta,'$.vendor') FROM device LIMIT 5"),
            ("The ->> shorthand", "SELECT name,meta ->> '$.firmware' FROM device LIMIT 5"),
            ("An object becomes rows", "SELECT d.name,j.key,j.value FROM device d,json_each(d.meta) j WHERE d.name='cnc-01'"),
        ]:
            print("\n--",title,"\n",query)
            for row in con.execute(query):print(row)
        con.execute("CREATE INDEX ix_device_vendor ON device(json_extract(meta,'$.vendor'))")
        con.commit()
        exact = "SELECT name FROM device WHERE json_extract(meta,'$.vendor')='Fanuc'"
        shorthand = "SELECT name FROM device WHERE meta ->> 'vendor'='Fanuc'"
        plans={}
        for name,query in [("indexed",exact),("shorthand",shorthand)]:
            plans[name]=[row[3] for row in con.execute("EXPLAIN QUERY PLAN "+query)]
            print("\n",query)
            print("\n".join(plans[name]))
        a=sorted(con.execute(exact).fetchall())
        b=sorted(con.execute(shorthand).fetchall())
        assert a==b and len(a)==334
        assert any("SEARCH" in p and "ix_device_vendor" in p for p in plans["indexed"])
        assert any("SCAN device" in p for p in plans["shorthand"])
        print("Matching Fanuc rows:",len(a))
        con.execute("SAVEPOINT invalid_probe")
        try:
            con.execute("INSERT INTO device(name,meta) VALUES (?,?)",("bad",'{"vendor":'))
        except sqlite3.IntegrityError as exc:
            invalid_error=str(exc)
            print("Invalid JSON rejected:",invalid_error)
        else:
            raise AssertionError("Invalid JSON accepted")
        finally:
            con.execute("ROLLBACK TO invalid_probe")
            con.execute("RELEASE invalid_probe")
        # A valid JSON scalar still passes: syntax is not an object schema.
        con.execute("SAVEPOINT shape_probe")
        con.execute("INSERT INTO device(name,meta) VALUES ('scalar','42')")
        print("Valid scalar accepted:",con.execute("SELECT json_type(meta) FROM device WHERE name='scalar'").fetchone())
        con.execute("ROLLBACK TO shape_probe")
        con.execute("RELEASE shape_probe")
        before=[row[1] for row in con.execute("PRAGMA table_info(device)")]
        with con:
            con.execute("UPDATE device SET meta=json_set(meta,'$.service_interval_days',180) WHERE name='cnc-01'")
        after=[row[1] for row in con.execute("PRAGMA table_info(device)")]
        assert before==after==["device_id","name","meta"]
        print("New vendor field, no column migration:",con.execute(
            "SELECT name,json_extract(meta,'$.service_interval_days') FROM device WHERE name='cnc-01'").fetchone())
        print("Columns before/after:",before,after)
        assert con.execute("SELECT COUNT(*) FROM device").fetchone()[0]==1000
        assert con.execute("PRAGMA integrity_check").fetchone()==("ok",)
        result={"sqlite":sqlite3.sqlite_version,"rows":1000,"fanuc_rows":len(a),
                "queries":{"indexed":exact,"shorthand":shorthand},"plans":plans,
                "invalid_json_error":invalid_error,"columns_unchanged":True}
        (OUT/"json-results.json").write_text(json.dumps(result,indent=2)+"\n")


if __name__=="__main__":main()
