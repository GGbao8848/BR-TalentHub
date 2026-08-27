"""学校管理：/api/schools*（CRUD + 绑定岗位 + 激活 + 二维码）。"""
import json

from fastapi import APIRouter, HTTPException

from app import database as db
from app.schemas import SchoolPayload, SchoolPositionsPayload

router = APIRouter()


def _school_out(school: dict) -> dict:
    """学校记录 → 前端展示结构（把绑定岗位 JSON 展开为详情）。"""
    pos_ids = json_loads(school.get("positions") or "[]")
    positions = []
    for pid in pos_ids:
        p = db.get_position(pid)
        if p:
            positions.append({"id": p["id"], "name": p["name"]})
    return {
        "id": school["id"],
        "name": school["name"],
        "position_ids": pos_ids,
        "positions": positions,
        "created_at": school["created_at"],
    }


def json_loads(s: str) -> list:
    try:
        return json.loads(s)
    except Exception:
        return []


@router.get("/api/schools")
def list_schools():
    return [_school_out(s) for s in db.list_schools()]


@router.post("/api/schools")
def create_school(payload: SchoolPayload):
    name = payload.name.strip()
    position_ids = payload.positions or []
    if not name:
        raise HTTPException(400, "学校名称不能为空")
    if db.school_name_exists(name):
        raise HTTPException(400, f"学校「{name}」已存在")
    valid = [pid for pid in position_ids if db.get_position(pid)]
    school_id = db.add_school(name, valid)
    return _school_out(db.get_school(school_id))


@router.put("/api/schools/{school_id}/positions")
def update_school_positions(school_id: int, payload: SchoolPositionsPayload):
    school = db.get_school(school_id)
    if not school:
        raise HTTPException(404, "学校不存在")
    valid = [pid for pid in payload.positions if db.get_position(pid)]
    db.update_school_positions(school_id, valid)
    return _school_out(db.get_school(school_id))


@router.delete("/api/schools/{school_id}")
def delete_school(school_id: int):
    if not db.delete_school(school_id):
        raise HTTPException(404, "学校不存在")
    return {"ok": True}


@router.post("/api/schools/{school_id}/activate")
def activate_school(school_id: int):
    """将某学校设为当前招聘会学校（现场大屏切换用）。"""
    school = db.get_school(school_id)
    if not school:
        raise HTTPException(404, "学校不存在")
    db.set_setting("active_school", school["name"])
    db.set_setting("updated_at", _now_str())
    return {"ok": True, "school": school["name"]}


def _now_str() -> str:
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@router.get("/api/options")
def get_options(school: str = ""):
    """手机端下拉数据源：学校列表 + 指定学校的岗位列表。"""
    schools = [_school_out(s) for s in db.list_schools()]
    positions = []
    if school:
        s = db.get_school_by_name(school)
        if s:
            positions = _school_out(s)["positions"]
    return {
        "schools": [{"id": s["id"], "name": s["name"]} for s in schools],
        "positions": positions,
        "school": school,
    }
