"""Run the local JSON and session checks and render the saved PostgreSQL evidence."""
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
OUT=HERE/"evidence"
OUT.mkdir(exist_ok=True)
for script,target in [("json_bench.py","json-output.txt"),("kv_compare.py","kv-output.txt")]:
    result=subprocess.run([sys.executable,str(HERE/script)],capture_output=True,text=True,timeout=180)
    if result.returncode:raise SystemExit(result.stdout+result.stderr)
    (OUT/target).write_text(result.stdout)
    print("Saved",target,flush=True)
subprocess.run([sys.executable,str(HERE/"write_notes.py")],check=True)
