import os
import sqlite3
from typing import List, Tuple, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "projects.db")


def _get_conn():
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "data"), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            length_ft REAL,
            width_ft REAL,
            depth_in REAL,
            area_sqft REAL,
            volume_cuft REAL,
            tons REAL,
            deleted INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.commit()
    conn.close()


def save_project(data: Dict[str, Any]) -> None:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO projects (
            project_name, length_ft, width_ft, depth_in,
            area_sqft, volume_cuft, tons, deleted
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """,
        (
            data.get("project_name"),
            data.get("length_ft"),
            data.get("width_ft"),
            data.get("depth_in"),
            data.get("area_sqft"),
            data.get("volume_cuft"),
            data.get("tons"),
        ),
    )
    conn.commit()
    conn.close()


def get_projects(active_only: bool = True, deleted_only: bool = False) -> List[Tuple]:
    conn = _get_conn()
    cur = conn.cursor()

    if deleted_only:
        cur.execute(
            "SELECT * FROM projects WHERE deleted = 1 ORDER BY created_at DESC"
        )
    elif active_only:
        cur.execute(
            "SELECT * FROM projects WHERE deleted = 0 ORDER BY created_at DESC"
        )
    else:
        cur.execute("SELECT * FROM projects ORDER BY created_at DESC")

    rows = cur.fetchall()
    conn.close()
    return [tuple(r) for r in rows]


def delete_project(project_id: int) -> None:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE projects SET deleted = 1 WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()


def restore_project(project_id: int) -> None:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE projects SET deleted = 0 WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()
