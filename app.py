import json
import os
import time
from datetime import datetime
import sqlite3
from typing import Any, Dict, List

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency
    OpenAI = None  # type: ignore[assignment]

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


def _log_query(*, query: str, rows_count: int, duration_ms: float | None, error: str | None) -> None:
    """Append a JSON line to the queries log. Controlled via env:
    - LOG_QUERIES: enable/disable (default on)
    - LOG_FILE: path to log file (default queries.log)
    """
    enabled = os.environ.get("LOG_QUERIES", "1").strip().lower() in {"1", "true", "yes", "on"}
    if not enabled:
        return
    event = {
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "sql": query,
        "rows_count": rows_count,
        "duration_ms": duration_ms,
        "error": error,
    }
    try:
        path = os.environ.get("LOG_FILE", "queries.log")
        with open(path, "a", encoding="utf-8") as f:
            json.dump(event, f, ensure_ascii=False)
            f.write("\n")
    except Exception:
        # Never fail due to logging issues
        pass


def run_sql(conn: sqlite3.Connection, query: str, limit: int = 100) -> Dict[str, Any]:
    """Execute SQL while keeping the result JSON-serialisable for tool calls."""
    started = time.perf_counter()
    try:
        limit_value = int(limit)
    except (TypeError, ValueError):  # pragma: no cover - defensive branch
        limit_value = 100
    limit_value = max(1, min(500, limit_value))
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchmany(limit_value + 1)
            truncated = len(rows) > limit_value
            rows = rows[:limit_value]
            serialised_rows: List[List[Any]] = [list(row) for row in rows]
            result = {
                "ok": True,
                "type": "rows",
                "columns": columns,
                "rows": serialised_rows,
                "row_count": len(serialised_rows),
                "truncated": truncated,
            }
            _log_query(query=query, rows_count=len(serialised_rows), duration_ms=round((time.perf_counter() - started) * 1000, 2), error=None)
            return result

        if conn.in_transaction:
            conn.commit()
        affected = cursor.rowcount if cursor.rowcount != -1 else 0
        result = {
            "ok": True,
            "type": "status",
            "row_count": affected,
            "message": f"{affected} rows affected.",
        }
        _log_query(query=query, rows_count=affected, duration_ms=round((time.perf_counter() - started) * 1000, 2), error=None)
        return result
    except sqlite3.Error as exc:  # pragma: no cover - defensive branch
        if conn.in_transaction:
            conn.rollback()
        _log_query(query=query, rows_count=0, duration_ms=round((time.perf_counter() - started) * 1000, 2), error=str(exc))
        return {"ok": False, "error": str(exc)}
    finally:
        cursor.close()


def ensure_openai_client() -> "OpenAI":
    if OpenAI is None:  # pragma: no cover - optional dependency guard
        raise RuntimeError("openai package is not installed")
    return OpenAI()


def tool_definitions() -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "get_schema",
                "description": "Return the current SQL schema as text. Use before writing SQL or when structure may have changed.",
                "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_sql",
                "description": "Execute a SQL statement against the connected SQLite database and get back the results.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The SQL statement to run. Must be valid SQLite syntax.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of rows to return (1-500).",
                            "minimum": 1,
                            "maximum": 500,
                            "default": 100,
                        },
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "finish",
                "description": "Send the final answer back to the user. Always call this when you are done reasoning and ready to respond.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "response": {
                            "type": "string",
                            "description": "Human-readable answer that will be shown to the user.",
                        }
                    },
                    "required": ["response"],
                    "additionalProperties": False,
                },
            },
        },
    ]


def process_tool_call(
    name: str,
    arguments: Dict[str, Any],
    conn: sqlite3.Connection,
) -> Dict[str, Any]:
    if name == "get_schema":
        return {"schema": get_schema(conn)}
    if name == "run_sql":
        query = arguments.get("query")
        if not isinstance(query, str):
            return {"ok": False, "error": "Missing SQL query text."}
        limit = arguments.get("limit", 100)
        return run_sql(conn, query, limit)
    if name == "finish":
        return {"ack": True, "response": arguments.get("response", "")}
    return {"ok": False, "error": f"Unknown tool: {name}"}


def chat_loop(conn: sqlite3.Connection) -> None:
    client = ensure_openai_client()
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    system_prompt = (
        "You are a meticulous SQLite analyst. Use the available tools to inspect the schema and run SQL. "
        "Always call the 'finish' tool with a clear, Hungarian user-facing answer when you are ready to respond."
    )

    history: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
    tools = tool_definitions()

    exit_words = {"exit", "quit", "kilep", "kilép", "q"}

    while True:
        try:
            user_message = input("👤 Kérdés (exit a kilépéshez): ").strip()
        except EOFError:  # pragma: no cover - CLI convenience
            print()
            break
        except KeyboardInterrupt:  # pragma: no cover - CLI convenience
            print("\nKilépés...")
            break

        if not user_message:
            continue
        if user_message.lower() in exit_words:
            print("Kilépés...")
            break

        history.append({"role": "user", "content": user_message})

        while True:
            response = client.chat.completions.create(
                model=model,
                messages=history,
                tools=tools,
                temperature=0,
            )
            message = response.choices[0].message

            assistant_entry: Dict[str, Any] = {"role": "assistant"}
            if message.content:
                assistant_entry["content"] = message.content
            if message.tool_calls:
                assistant_entry["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ]
            history.append(assistant_entry)

            if not message.tool_calls:
                content = (message.content or "").strip()
                if content:
                    print(f"🤖 {content}")
                break

            finish_called = False
            for tool_call in message.tool_calls:
                try:
                    arguments = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    arguments = {}
                    tool_result = {"ok": False, "error": "Invalid JSON arguments received."}
                else:
                    tool_result = process_tool_call(tool_call.function.name, arguments, conn)

                history.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result, ensure_ascii=False),
                    }
                )

                if tool_call.function.name == "finish":
                    finish_called = True
                    response_text = tool_result.get("response", "").strip()
                    if response_text:
                        print(f"🤖 {response_text}")

            if finish_called:
                break




def main() -> None:
    load_dotenv()
    db_path = os.environ.get("DATABASE_PATH")
    if not db_path:
        raise SystemExit("DATABASE_PATH environment variable not set")

    conn = sqlite3.connect(db_path)

    try:
        chat_loop(conn)
    except Exception as exc:  # pragma: no cover - runtime errors
        print("Hiba:", exc)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
