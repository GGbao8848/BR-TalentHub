"""SQLite 数据层：招聘会配置、岗位、学校、上传记录。"""
import json
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


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}


def init_db() -> None:
    conn = get_conn()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS positions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            requirement TEXT DEFAULT '',
            created_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS schools (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            positions   TEXT DEFAULT '[]',   -- JSON 数组，存绑定的岗位 ID
            created_at  TEXT NOT NULL
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
    # 兼容迁移：resumes 表增加学校/岗位关联列（旧库无此列时补充）
    cols = _columns(conn, "resumes")
    if "school_id" not in cols:
        conn.execute("ALTER TABLE resumes ADD COLUMN school_id INTEGER DEFAULT NULL")
    if "position_id" not in cols:
        conn.execute("ALTER TABLE resumes ADD COLUMN position_id INTEGER DEFAULT NULL")
    conn.commit()
    conn.close()


# ---------------------------------------------------------------- 通用设置

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


# ---------------------------------------------------------------- 岗位

def add_position(name: str, requirement: str = "") -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO positions(name, requirement, created_at) VALUES(?, ?, ?)",
        (name.strip(), (requirement or "").strip(), _now()),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def list_positions() -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, name, requirement, created_at FROM positions ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_position(position_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM positions WHERE id=?", (position_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_position(position_id: int) -> bool:
    conn = get_conn()
    cur = conn.execute("DELETE FROM positions WHERE id=?", (position_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted


def update_position(position_id: int, name: str, requirement: str) -> bool:
    conn = get_conn()
    cur = conn.execute(
        "UPDATE positions SET name=?, requirement=? WHERE id=?",
        (name.strip(), (requirement or "").strip(), position_id),
    )
    conn.commit()
    updated = cur.rowcount > 0
    conn.close()
    return updated


def position_name_exists(name: str, exclude_id: int | None = None) -> bool:
    conn = get_conn()
    if exclude_id:
        row = conn.execute(
            "SELECT id FROM positions WHERE name=? AND id<>?", (name.strip(), exclude_id)
        ).fetchone()
    else:
        row = conn.execute("SELECT id FROM positions WHERE name=?", (name.strip(),)).fetchone()
    conn.close()
    return row is not None


# ---------------------------------------------------------------- 学校

def add_school(name: str, position_ids: list[int] | None = None) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO schools(name, positions, created_at) VALUES(?, ?, ?)",
        (name.strip(), json.dumps(position_ids or [], ensure_ascii=False), _now()),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_school_positions(school_id: int, position_ids: list[int]) -> None:
    conn = get_conn()
    conn.execute(
        "UPDATE schools SET positions=? WHERE id=?",
        (json.dumps(position_ids, ensure_ascii=False), school_id),
    )
    conn.commit()
    conn.close()


def list_schools() -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, name, positions, created_at FROM schools ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_school(school_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM schools WHERE id=?", (school_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_school_by_name(name: str) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM schools WHERE name=?", (name.strip(),)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_school(school_id: int) -> bool:
    conn = get_conn()
    cur = conn.execute("DELETE FROM schools WHERE id=?", (school_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted


def school_name_exists(name: str, exclude_id: int | None = None) -> bool:
    conn = get_conn()
    if exclude_id:
        row = conn.execute(
            "SELECT id FROM schools WHERE name=? AND id<>?", (name.strip(), exclude_id)
        ).fetchone()
    else:
        row = conn.execute("SELECT id FROM schools WHERE name=?", (name.strip(),)).fetchone()
    conn.close()
    return row is not None


# ---------------------------------------------------------------- 简历

def add_resume(data: dict) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO resumes(name, phone, position, original, filename, filepath, "
        "filesize, upload_time, ip, school_id, position_id) "
        "VALUES(:name, :phone, :position, :original, :filename, :filepath, "
        ":filesize, :upload_time, :ip, :school_id, :position_id)",
        data,
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def list_resumes(limit: int = 50) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT r.*, s.name AS school_name, p.name AS position_name "
        "FROM resumes r "
        "LEFT JOIN schools s ON r.school_id = s.id "
        "LEFT JOIN positions p ON r.position_id = p.id "
        "ORDER BY r.id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def query_resumes(
    school: str = "",
    position: str = "",
    keyword: str = "",
    date: str = "",
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """简历列表：按 学校/岗位/关键词/日期 筛选，分页返回（含总数）。"""
    where, params = [], []
    if school:
        where.append("s.name = ?")
        params.append(school)
    if position:
        where.append("p.name = ?")
        params.append(position)
    if keyword:
        like = f"%{keyword}%"
        where.append("(r.name LIKE ? OR r.phone LIKE ? OR r.original LIKE ?)")
        params += [like, like, like]
    if date:
        where.append("substr(r.upload_time, 1, 10) = ?")
        params.append(date)
    clause = (" WHERE " + " AND ".join(where)) if where else ""

    conn = get_conn()
    total = conn.execute(
        "SELECT COUNT(*) AS c FROM resumes r "
        "LEFT JOIN schools s ON r.school_id = s.id "
        "LEFT JOIN positions p ON r.position_id = p.id" + clause,
        params,
    ).fetchone()["c"]
    rows = conn.execute(
        "SELECT r.*, s.name AS school_name, p.name AS position_name "
        "FROM resumes r "
        "LEFT JOIN schools s ON r.school_id = s.id "
        "LEFT JOIN positions p ON r.position_id = p.id" + clause +
        " ORDER BY r.id DESC LIMIT ? OFFSET ?",
        params + [limit, offset],
    ).fetchall()
    conn.close()
    return {"total": total, "items": [dict(r) for r in rows]}


def delete_resume(resume_id: int) -> bool:
    conn = get_conn()
    cur = conn.execute("DELETE FROM resumes WHERE id=?", (resume_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted


def count_resumes() -> int:
    conn = get_conn()
    n = conn.execute("SELECT COUNT(*) AS c FROM resumes").fetchone()["c"]
    conn.close()
    return n


def get_resume(resume_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT r.*, s.name AS school_name, p.name AS position_name "
        "FROM resumes r "
        "LEFT JOIN schools s ON r.school_id = s.id "
        "LEFT JOIN positions p ON r.position_id = p.id "
        "WHERE r.id=?",
        (resume_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------------------------------------------------------- 看板统计

def dashboard_stats() -> dict:
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) AS c FROM resumes").fetchone()["c"]

    by_school = [
        dict(r)
        for r in conn.execute(
            "SELECT COALESCE(s.name, '未分类') AS name, COUNT(*) AS count "
            "FROM resumes r LEFT JOIN schools s ON r.school_id = s.id "
            "GROUP BY r.school_id ORDER BY count DESC"
        )
    ]

    by_position = [
        dict(r)
        for r in conn.execute(
            "SELECT COALESCE(p.name, '未分类') AS name, COUNT(*) AS count "
            "FROM resumes r LEFT JOIN positions p ON r.position_id = p.id "
            "GROUP BY r.position_id ORDER BY count DESC"
        )
    ]

    by_day = [
        dict(r)
        for r in conn.execute(
            "SELECT substr(upload_time, 1, 10) AS day, COUNT(*) AS count "
            "FROM resumes GROUP BY day ORDER BY day DESC LIMIT 7"
        )
    ]
    by_day.reverse()
    conn.close()
    return {
        "total": total,
        "by_school": by_school,
        "by_position": by_position,
        "by_day": by_day,
    }


def _now() -> str:
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
