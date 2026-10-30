"""SQLite 数据层：建库建表（含迁移），todos / notes / messages / settings 增删改查。"""

import sqlite3
from datetime import datetime
from pathlib import Path

# 数据库文件固定在项目根目录（app/db/ 的上两级），与工作目录无关
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = str(PROJECT_ROOT / "inbox.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """建库建表 + 轻量迁移（幂等，可重复执行）。"""
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
            """
        )
        # 旧库迁移：todos 表补 done 列
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(todos)")}
        if "done" not in cols:
            conn.execute(
                "ALTER TABLE todos ADD COLUMN done INTEGER NOT NULL DEFAULT 0"
            )
        conn.commit()
    finally:
        conn.close()


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------- Todos ----------

def add_todo(content: str) -> dict:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO todos (content, created_at) VALUES (?, ?)",
            (content, _now()),
        )
        conn.commit()
        return get_todo(int(cur.lastrowid))
    finally:
        conn.close()


def get_todo(todo_id: int) -> dict:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, content, done, created_at FROM todos WHERE id = ?",
            (todo_id,),
        ).fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


def get_todos() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, content, done, created_at FROM todos "
            "ORDER BY done ASC, id DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def set_todo_done(todo_id: int, done: bool) -> dict:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE todos SET done = ? WHERE id = ?",
            (1 if done else 0, todo_id),
        )
        conn.commit()
    finally:
        conn.close()
    return get_todo(todo_id)


def update_todo(todo_id: int, content: str) -> dict:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE todos SET content = ? WHERE id = ?", (content, todo_id)
        )
        conn.commit()
    finally:
        conn.close()
    return get_todo(todo_id)


def delete_todo(todo_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        conn.commit()
    finally:
        conn.close()


# ---------- Notes ----------

def add_note(content: str) -> dict:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO notes (content, created_at) VALUES (?, ?)",
            (content, _now()),
        )
        conn.commit()
        return get_note(int(cur.lastrowid))
    finally:
        conn.close()


def get_note(note_id: int) -> dict:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, content, created_at FROM notes WHERE id = ?", (note_id,)
        ).fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


def get_notes() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, content, created_at FROM notes ORDER BY id DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def update_note(note_id: int, content: str) -> dict:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE notes SET content = ? WHERE id = ?", (content, note_id)
        )
        conn.commit()
    finally:
        conn.close()
    return get_note(note_id)


def delete_note(note_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        conn.commit()
    finally:
        conn.close()


# ---------- 对话记录 ----------

def add_message(role: str, content: str) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO messages (role, content, created_at) VALUES (?, ?, ?)",
            (role, content, _now()),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def get_messages(limit: int = 100) -> list[dict]:
    """返回最近 limit 条对话，按时间正序。"""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, role, content, created_at FROM ("
            "  SELECT * FROM messages ORDER BY id DESC LIMIT ?"
            ") ORDER BY id ASC",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def clear_messages() -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM messages")
        conn.commit()
    finally:
        conn.close()


# ---------- 设置（key-value） ----------

def get_settings() -> dict:
    """返回 settings 表中已保存的全部配置。"""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
        return {row["key"]: row["value"] for row in rows}
    finally:
        conn.close()


def set_setting(key: str, value: str) -> None:
    from app.core.config import SETTING_KEYS

    if key not in SETTING_KEYS:
        raise ValueError(f"不支持的配置项: {key}")
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        conn.commit()
    finally:
        conn.close()
