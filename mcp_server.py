"""Model Context Protocol server exposing the same SQLite tools as the CLI app."""
from __future__ import annotations

import asyncio
import os
import sqlite3
from functools import partial
from typing import Annotated, Any, Callable, TypeVar

from app import get_schema as fetch_schema
from app import run_sql as execute_sql

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    def load_dotenv() -> bool:  # type: ignore[return-type]
        return False

T = TypeVar("T")


def _get_database_path() -> str:
    """Return the configured SQLite database path or raise a helpful error."""
    db_path = os.environ.get("DATABASE_PATH")
    if not db_path:
        raise RuntimeError("DATABASE_PATH environment variable not set")
    return db_path


def _with_connection(func: Callable[[sqlite3.Connection], T]) -> T:
    """Open a fresh connection, run ``func`` with it, and close afterwards."""
    conn = sqlite3.connect(_get_database_path())
    try:
        return func(conn)
    finally:
        conn.close()


async def _with_connection_async(func: Callable[[sqlite3.Connection], T]) -> T:
    """Execute ``func`` in a worker thread to keep the async loop responsive."""
    return await asyncio.to_thread(_with_connection, func)


def build_server() -> "FastMCP":
    """Create and return the configured MCP server instance."""
    try:
        from mcp.server.fastmcp import Context, FastMCP
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "The 'mcp' package is required to run the MCP server. Install it with `pip install mcp`."
        ) from exc

    mcp = FastMCP("sqlite-demo-tools")

    @mcp.tool(
        name="get_schema",
        description=(
            "Return the current SQL schema as text. Use before writing SQL or when the structure may have changed."
        ),
    )
    async def get_schema(context: Any) -> str:
        return await _with_connection_async(fetch_schema)

    @mcp.tool(
        name="run_sql",
        description="Execute a SQL statement against the connected SQLite database and get back the results.",
    )
    async def run_sql(
        context: Any,
        query: Annotated[str, "The SQL statement to run. Must be valid SQLite syntax."],
        limit: Annotated[int, "Maximum number of rows to return (1-500)."] = 100,
    ) -> dict[str, Any]:
        return await _with_connection_async(partial(execute_sql, query=query, limit=limit))

    return mcp


def main() -> None:
    load_dotenv()
    try:
        # Ensure the configuration is sane before we start listening for MCP clients.
        _get_database_path()
        server = build_server()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    server.run()


if __name__ == "__main__":
    main()