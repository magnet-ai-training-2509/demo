import os
import sqlite3
from typing import Any, List

try:
    import openai
except ImportError:  # pragma: no cover - optional dependency
    openai = None

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    def load_dotenv() -> bool:
        return False


def get_schema(conn: sqlite3.Connection) -> str:
    """Return a textual representation of the database schema."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )
    tables: List[str] = []
    for (name,) in cursor.fetchall():
        col_cursor = conn.execute(f"PRAGMA table_info('{name}')")
        cols = [f"{col[1]} {col[2]}" for col in col_cursor.fetchall()]
        tables.append(f"Table {name}: " + ", ".join(cols))
    return "\n".join(tables)


def generate_sql(question: str, schema: str) -> str:
    """Use OpenAI to translate a natural language question into SQL."""
    if openai is None:
        raise RuntimeError("openai package is not installed")
    system = (
        "You are an assistant that converts natural language questions to SQL "
        "queries. Use only the provided schema and do not hallucinate." 
    )
    prompt = f"Schema:\n{schema}\nQuestion: {question}\nSQL:"
    completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    return completion.choices[0].message.content.strip()


def run_query(conn: sqlite3.Connection, sql: str) -> List[tuple[Any]]:
    cursor = conn.execute(sql)
    return cursor.fetchall()


def main() -> None:
    load_dotenv()
    db_path = os.environ.get("DATABASE_PATH")
    if not db_path:
        raise SystemExit("DATABASE_PATH environment variable not set")

    conn = sqlite3.connect(db_path)
    schema = get_schema(conn)

    try:
        question = input("Kérdés természetes nyelven: ")
        sql = generate_sql(question, schema)
        rows = run_query(conn, sql)
        print("SQL:", sql)
        for row in rows:
            print(row)
    except Exception as exc:  # pragma: no cover - runtime errors
        print("Hiba:", exc)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
