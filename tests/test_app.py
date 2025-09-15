import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import get_schema


def test_get_schema_contains_table_and_columns():
    conn = sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)')
    schema = get_schema(conn)
    assert 'users' in schema
    assert 'id INTEGER' in schema
    assert 'name TEXT' in schema
