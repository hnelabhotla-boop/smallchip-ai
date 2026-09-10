"""
olp_db.py — SQLite storage for OLP drag logs and expert verification.

Two tables:
- drag_log: every expert drag-to-re-place
- expert_verification: which users are verified experts (and how)
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Optional

DB_PATH = Path("/Users/harshith/Documents/ChipPlacer/data/olp.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def init_db():
    """Create tables if they don't exist."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS drag_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            chip_id TEXT NOT NULL,
            cell_id TEXT NOT NULL,
            before_x REAL NOT NULL,
            before_y REAL NOT NULL,
            after_x REAL NOT NULL,
            after_y REAL NOT NULL,
            priority_hpwl REAL,
            priority_cong REAL,
            priority_therm REAL,
            priority_timing REAL,
            hpwl_before REAL,
            hpwl_after REAL,
            features_json TEXT,
            is_synthetic INTEGER DEFAULT 0,
            timestamp REAL NOT NULL
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS expert_verification (
            user_id TEXT PRIMARY KEY,
            verified_at REAL NOT NULL,
            verification_method TEXT NOT NULL,
            source_def_path TEXT,
            source_chip_cells INTEGER,
            source_tool TEXT,
            drag_count INTEGER DEFAULT 0
        )
        """
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_drag_user ON drag_log(user_id)"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_drag_chip ON drag_log(chip_id)"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_drag_synthetic ON drag_log(is_synthetic)"
    )
    conn.commit()
    conn.close()


def get_db():
    """Open a connection to the OLP database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


class DragLog:
    """Record of a single drag-to-re-place event."""

    def __init__(
        self,
        user_id: str,
        chip_id: str,
        cell_id: str,
        before_x: float,
        before_y: float,
        after_x: float,
        after_y: float,
        priority: dict,
        hpwl_before: float,
        hpwl_after: float,
        features: Optional[dict] = None,
        is_synthetic: bool = False,
    ):
        self.user_id = user_id
        self.chip_id = chip_id
        self.cell_id = cell_id
        self.before_x = before_x
        self.before_y = before_y
        self.after_x = after_x
        self.after_y = after_y
        self.priority = priority
        self.hpwl_before = hpwl_before
        self.hpwl_after = hpwl_after
        self.features = features or {}
        self.is_synthetic = is_synthetic
        self.timestamp = time.time()

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "chip_id": self.chip_id,
            "cell_id": self.cell_id,
            "before_x": self.before_x,
            "before_y": self.before_y,
            "after_x": self.after_x,
            "after_y": self.after_y,
            "priority": self.priority,
            "hpwl_before": self.hpwl_before,
            "hpwl_after": self.hpwl_after,
            "delta_hpwl": self.hpwl_before - self.hpwl_after,  # positive = improvement
            "delta_x": self.after_x - self.before_x,
            "delta_y": self.after_y - self.before_y,
            "features": self.features,
            "is_synthetic": self.is_synthetic,
            "timestamp": self.timestamp,
        }

    def save(self):
        conn = get_db()
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO drag_log
            (user_id, chip_id, cell_id, before_x, before_y, after_x, after_y,
             priority_hpwl, priority_cong, priority_therm, priority_timing,
             hpwl_before, hpwl_after, features_json, is_synthetic, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.user_id, self.chip_id, self.cell_id,
                self.before_x, self.before_y, self.after_x, self.after_y,
                self.priority.get("hpwl", 1.0),
                self.priority.get("congestion", 0.0),
                self.priority.get("thermal", 0.0),
                self.priority.get("timing", 0.0),
                self.hpwl_before, self.hpwl_after,
                json.dumps(self.features),
                1 if self.is_synthetic else 0,
                self.timestamp,
            ),
        )
        conn.commit()
        # Update user's drag count
        c.execute(
            """
            UPDATE expert_verification
            SET drag_count = drag_count + 1
            WHERE user_id = ?
            """,
            (self.user_id,),
        )
        conn.commit()
        conn.close()


class ExpertVerification:
    """A user's verified-expert status."""

    def __init__(self, user_id, method, source_def_path=None,
                 source_chip_cells=None, source_tool=None):
        self.user_id = user_id
        self.verified_at = time.time()
        self.method = method  # "industry_def_upload", "faculty_referral", "manual"
        self.source_def_path = source_def_path
        self.source_chip_cells = source_chip_cells
        self.source_tool = source_tool
        self.drag_count = 0

    def save(self):
        conn = get_db()
        c = conn.cursor()
        c.execute(
            """
            INSERT OR REPLACE INTO expert_verification
            (user_id, verified_at, verification_method, source_def_path,
             source_chip_cells, source_tool, drag_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.user_id, self.verified_at, self.method,
                self.source_def_path, self.source_chip_cells,
                self.source_tool, self.drag_count,
            ),
        )
        conn.commit()
        conn.close()


def is_verified_expert(user_id: str) -> bool:
    """Check if a user is a verified expert."""
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "SELECT 1 FROM expert_verification WHERE user_id = ?",
        (user_id,),
    )
    result = c.fetchone() is not None
    conn.close()
    return result


def count_drags(user_id: Optional[str] = None, synthetic_only: bool = False) -> int:
    """Count drags, optionally filtered by user or synthetic status."""
    conn = get_db()
    c = conn.cursor()
    if user_id:
        c.execute(
            "SELECT COUNT(*) FROM drag_log WHERE user_id = ?",
            (user_id,),
        )
    elif synthetic_only:
        c.execute(
            "SELECT COUNT(*) FROM drag_log WHERE is_synthetic = 1"
        )
    else:
        c.execute("SELECT COUNT(*) FROM drag_log")
    n = c.fetchone()[0]
    conn.close()
    return n
