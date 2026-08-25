"""SQLite 数据层：招聘会配置、上传记录。"""
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "br_talenthub.db"


def get_conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    conn = get_conn()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS resumes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT DEFAULT '',
            phone       TEXT DEFAULT '',
            position    TEXT DEFAULT '',
            original    TEXT NOT NULL,          -- 用户上传的原始文件名
            filename    TEXT NOT NULL,          -- 落盘文件名
            filepath    TEXT NOT NULL,          -- 绝对路径
            filesize    INTEGER DEFAULT 0,
            upload_time TEXT NOT NULL,
            ip          TEXT DEFAULT ''
        );
        """
    )
    conn.commit()
    conn.close()


def get_setting(key: str, default: str | None = None) -> str | None:
    conn = get_conn()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO settings(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()


def add_resume(data: dict) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO resumes(name, phone, position, original, filename, filepath, "
        "filesize, upload_time, ip) VALUES(:name, :phone, :position, :original, "
        ":filename, :filepath, :filesize, :upload_time, :ip)",
        data,
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def list_resumes(limit: int = 50) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM resumes ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_resumes() -> int:
    conn = get_conn()
    n = conn.execute("SELECT COUNT(*) AS c FROM resumes").fetchone()["c"]
    conn.close()
    return n


def get_resume(resume_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM resumes WHERE id=?", (resume_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None
