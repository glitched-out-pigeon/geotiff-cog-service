# app/db.py
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "layers.db"


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS layers (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                bounds TEXT,
                original_size_mb REAL,
                cog_size_mb REAL,
                compression_ratio REAL,
                error_message TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def create_layer(layer_id: str, filename: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO layers (id, filename, status, created_at) VALUES (?, ?, 'pending', ?)",
            (layer_id, filename, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()


def mark_layer_done(layer_id: str, bounds: list, original_size_mb: float,
                     cog_size_mb: float, compression_ratio: float) -> None:
    with get_connection() as conn:
        conn.execute(
            """UPDATE layers
               SET status = 'done', bounds = ?, original_size_mb = ?,
                   cog_size_mb = ?, compression_ratio = ?
               WHERE id = ?""",
            (json.dumps(bounds), original_size_mb, cog_size_mb, compression_ratio, layer_id),
        )
        conn.commit()


def mark_layer_failed(layer_id: str, error_message: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE layers SET status = 'failed', error_message = ? WHERE id = ?",
            (error_message, layer_id),
        )
        conn.commit()


def _row_to_dict(row) -> dict:
    d = dict(row)
    if d.get("bounds"):
        d["bounds"] = json.loads(d["bounds"])
    return d


def get_layer(layer_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM layers WHERE id = ?", (layer_id,)).fetchone()
        return _row_to_dict(row) if row else None


def list_layers() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM layers ORDER BY created_at DESC").fetchall()
        return [_row_to_dict(row) for row in rows]