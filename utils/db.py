"""
Database connection helper.
Returns a shared SQLite connection for the Streamlit session.
"""

import sqlite3
import os
import streamlit as st

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "fulfillment.db")


def get_connection() -> sqlite3.Connection:
    """Get or create a SQLite connection (cached per Streamlit session)."""
    if "db_conn" not in st.session_state:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        st.session_state["db_conn"] = conn
    return st.session_state["db_conn"]


def run_query(sql: str, params: tuple = ()) -> list[dict]:
    """Execute a SELECT and return list of dicts."""
    conn = get_connection()
    cur = conn.execute(sql, params)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def run_execute(sql: str, params: tuple = ()) -> None:
    """Execute an INSERT / UPDATE / DELETE and commit."""
    conn = get_connection()
    conn.execute(sql, params)
    conn.commit()

def run_transaction(queries: list[tuple[str, tuple]]) -> None:
    """Execute multiple queries in a single transaction."""
    conn = get_connection()
    try:
        for sql, params in queries:
            conn.execute(sql, params)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
