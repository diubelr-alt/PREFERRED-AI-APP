import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join("data", "projects.db")

def _get_conn():
    os.makedirs("data", exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

# ----------------------------------------------------
# INIT DB
# ----------------------------------------------------
def init_db():
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
            created_at TEXT
        );
        """
    )

    conn.commit()
    conn.close()

# ----------------------------------------------------
# SAVE PROJECT
# ----------------------------------------------------
def save_project(data: dict):
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO projects (
            project_name, length_ft, width_ft, depth_in,
            area_sqft, volume_cuft, tons, deleted, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
        """,
        (
            data["project_name"],
            data["length_ft"],
            data["width_ft"],
            data["depth_in"],
            data["area_sqft"],
            data["volume_cuft"],
            data["tons"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )

    conn.commit()
    conn.close()

# ----------------------------------------------------
# GET PROJECTS
# ----------------------------------------------------
def get_projects(active_only=True, deleted_only=False):
    conn = _get_conn()
    cur = conn.cursor()

    if active_only:
        cur.execute("SELECT * FROM projects WHERE deleted = 0 ORDER BY id DESC")
    elif deleted_only:
        cur.execute("SELECT * FROM projects WHERE deleted = 1 ORDER BY id DESC")
    else:
        cur.execute("SELECT * FROM projects ORDER BY id DESC")

    rows = cur.fetchall()
    conn.close()
    return rows

# ----------------------------------------------------
# DELETE PROJECT (MOVE TO TRASH)
# ----------------------------------------------------
def delete_project(pid: int):
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute("UPDATE projects SET deleted = 1 WHERE id = ?", (pid,))

    conn.commit()
    conn.close()

# ----------------------------------------------------
# RESTORE PROJECT
# ----------------------------------------------------
def restore_project(pid: int):
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute("UPDATE projects SET deleted = 0 WHERE id = ?", (pid,))

    conn.commit()
    conn.close()
