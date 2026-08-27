"""简历上传与管理：/api/resumes*（列表/删除/导出ZIP/单条下载）。"""
import re
import uuid
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response

from app import database as db

router = APIRouter()

ALLOWED_EXT = {".pdf", ".doc", ".docx"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


def _default_save_dir() -> Path:
    import os

    base = Path(__file__).resolve().parent.parent.parent
    data_dir = base / "data"
    env = os.environ.get("SAVE_DIR", "").strip()
    return Path(env) if env else Path(data_dir / "resumes")


def json_loads(s: str) -> list:
    import json

    try:
        return json.loads(s)
    except Exception:
        return []


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@router.post("/api/resumes/upload")
async def upload_resume(
    file: UploadFile = File(...),
    name: str = Form(""),
    phone: str = Form(""),
    position: str = Form(""),
    school: str = Form(""),
    position_id: int = Form(0),
):
    """手机端提交简历：校验（姓名/手机/岗位必填）→ 按 学校/岗位/文件 三级目录落盘 → 记录。"""
    name = (name or "").strip()
    phone = (phone or "").strip()
    position = (position or "").strip()
    school = (school or "").strip()

    if not name:
        raise HTTPException(400, "请填写姓名")
    if not phone:
        raise HTTPException(400, "请填写手机号")
    if not position:
        raise HTTPException(400, "请选择应聘岗位")

    # 解析学校（二维码带 school 参数则锁定，否则取第一个学校）
    school_row = db.get_school_by_name(school) if school else None
    if not school_row:
        schools = db.list_schools()
        if not schools:
            raise HTTPException(400, "暂未配置招聘学校，请联系现场工作人员")
        school_row = schools[0]
        school = school_row["name"]
    school_id = school_row["id"]

    # 岗位：优先用 position_id（来自下拉框），否则按名称匹配
    position_row = db.get_position(position_id) if position_id else None
    if not position_row:
        for p in db.list_positions():
            if p["name"] == position:
                position_row = p
                break
    if not position_row:
        raise HTTPException(400, f"岗位「{position}」不存在")
    position_id = position_row["id"]

    # 学校-岗位归属校验：岗位必须属于该学校绑定列表
    school_pos_ids = json_loads(school_row.get("positions") or "[]")
    if position_id not in school_pos_ids:
        raise HTTPException(400, f"岗位「{position_row['name']}」不属于学校「{school_row['name']}」")

    original = file.filename or "resume"
    ext = Path(original).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, "仅支持 PDF / DOC / DOCX 格式")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "文件超过 20MB 上限")

    safe_original = re.sub(r'[\\/:*?"<>|\r\n]', "_", original)

    base_dir = Path(db.get_setting("save_dir", "") or _default_save_dir())
    safe_school = re.sub(r'[\\/:*?"<>|\r\n]', "_", school)
    safe_position = re.sub(r'[\\/:*?"<>|\r\n]', "_", position)
    target_dir = base_dir / safe_school / safe_position
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        raise HTTPException(400, f"无法创建存储目录：{exc}")

    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    stored_name = f"{ts}_{uuid.uuid4().hex[:6]}{ext}"
    filepath = target_dir / stored_name
    filepath.write_bytes(content)

    record = {
        "name": name,
        "phone": phone,
        "position": position,
        "original": safe_original,
        "filename": stored_name,
        "filepath": str(filepath),
        "filesize": len(content),
        "upload_time": _now_str(),
        "ip": "",
        "school_id": school_id,
        "position_id": position_id,
    }
    resume_id = db.add_resume(record)
    return {"id": resume_id, "message": "上传成功", "filename": original}


@router.get("/api/resumes")
def list_resumes(
    school: str = "",
    position: str = "",
    keyword: str = "",
    date_start: str = "",
    date_end: str = "",
    limit: int = 100,
    offset: int = 0,
):
    """简历管理：按 学校/岗位/关键词/日期时间段 筛选，分页。"""
    limit = min(max(limit, 1), 500)
    offset = max(offset, 0)
    return db.query_resumes(
        school=school,
        position=position,
        keyword=keyword,
        date_start=date_start,
        date_end=date_end,
        limit=limit,
        offset=offset,
    )


@router.delete("/api/resumes/{resume_id}")
def delete_resume(resume_id: int):
    """删除单条简历记录（同时删除磁盘文件）。"""
    row = db.get_resume(resume_id)
    if not row:
        raise HTTPException(404, "记录不存在")
    try:
        Path(row["filepath"]).unlink(missing_ok=True)
    except Exception:
        pass
    db.delete_resume(resume_id)
    return {"ok": True}


@router.get("/api/resumes/export.zip")
def export_resumes(
    school: str = "",
    position: str = "",
    keyword: str = "",
    date_start: str = "",
    date_end: str = "",
    ids: str = "",
):
    """按当前筛选条件（或指定 ids）打包下载简历文件（ZIP）。

    文件名保留 学校/岗位 目录结构，便于会后归档。
    """
    if ids:
        id_list = [int(x) for x in ids.split(",") if x.strip().isdigit()]
        items = []
        for rid in id_list:
            row = db.get_resume(rid)
            if row:
                items.append(row)
    else:
        data = db.query_resumes(
            school=school,
            position=position,
            keyword=keyword,
            date_start=date_start,
            date_end=date_end,
            limit=500,
            offset=0,
        )
        items = data["items"]
    if not items:
        raise HTTPException(400, "没有符合条件的简历")

    buf = BytesIO()
    seen = {}
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for r in items:
            path = Path(r["filepath"])
            if not path.exists():
                continue
            base = Path(r["original"]).stem
            ext = Path(r["original"]).suffix
            folder = f"{r.get('school_name') or '未分类'}/{r.get('position_name') or '未分类'}"
            name = base + ext
            if name in seen:
                seen[name] += 1
                name = f"{base}_{seen[name]}{ext}"
            else:
                seen[name] = 0
            zf.write(path, arcname=f"{folder}/{name}")
    buf.seek(0)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="resumes_{stamp}.zip"'},
    )


@router.get("/api/resumes/{resume_id}/download")
def download_resume(resume_id: int):
    row = db.get_resume(resume_id)
    if not row:
        raise HTTPException(404, "记录不存在")
    path = Path(row["filepath"])
    if not path.exists():
        raise HTTPException(404, "文件已丢失")
    return FileResponse(path, filename=row["original"])
