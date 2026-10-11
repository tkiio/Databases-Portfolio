import platform
import sqlite3
import sys
from importlib.metadata import PackageNotFoundError, version

print("Python executable:", sys.executable)
print("Python version:", platform.python_version())
print("SQLite version:", sqlite3.sqlite_version)

for package in ("duckdb", "datasette", "sqlite-utils", "pydantic", "sqlalchemy"):
    try:
        print(f"{package}: {version(package)}")
    except PackageNotFoundError:
        print(f"{package}: NOT INSTALLED")