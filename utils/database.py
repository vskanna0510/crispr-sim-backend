"""SQLite database setup and helpers."""

import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "crispr_sim.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          TEXT PRIMARY KEY,
            sequence    TEXT NOT NULL,
            length      INTEGER,
            gc_percent  REAL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS simulations (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id          TEXT,
            original_sequence   TEXT,
            edited_sequence     TEXT,
            repair_type         TEXT,
            cut_position        INTEGER,
            frameshift          INTEGER,
            premature_stop      INTEGER,
            created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );

        CREATE TABLE IF NOT EXISTS pam_scans (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT,
            pam_count   INTEGER,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );
    """)

    conn.commit()
    conn.close()


def save_session(session_id: str, sequence: str, gc_percent: float) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO sessions (id, sequence, length, gc_percent) VALUES (?, ?, ?, ?)",
        (session_id, sequence, len(sequence), gc_percent),
    )
    conn.commit()
    conn.close()


def save_simulation(
    session_id: str,
    original: str,
    edited: str,
    repair_type: str,
    cut_position: int,
    frameshift: bool,
    premature_stop: bool,
) -> None:
    conn = get_connection()
    conn.execute(
        """INSERT INTO simulations
           (session_id, original_sequence, edited_sequence, repair_type,
            cut_position, frameshift, premature_stop)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (session_id, original, edited, repair_type, cut_position,
         int(frameshift), int(premature_stop)),
    )
    conn.commit()
    conn.close()
