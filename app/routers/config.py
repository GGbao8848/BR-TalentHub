"""配置与招聘会：/api/config /api/stats /api/qrcode /api/event/reset。"""
import socket
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path

import qrcode
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app import database as db
from app.schemas import ConfigPayload

router = APIRouter()


def get_local_ip() -> str:
    """探测本机局域网 IP（用于生成手机可访问的二维码链接）。"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect(("8.8.8.8", 80))  # UDP 不真正发包，仅用于取本机路由 IP
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def gen_event_id() -> str:
    """短 ID：给每个招聘会一个唯一标识，二维码里携带。"""
    return uuid.uuid4().hex[:6].upper()


def build_qr(url: str) -> Response:
    """生成二维码 PNG。"""
    qr = qrcode.QRCode(border=2, box_size=10, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@router.get("/api/config")
def get_config():
    """管理端/上传页共用：当前招聘会配置 + 局域网地址 + 统计。"""
    event_name = db.get_setting("event_name", "江苏北人智能制造科技股份有限公司")
    event_id = db.get_setting("event_id", gen_event_id())
    if not db.get_setting("event_id"):
        db.set_setting("event_id", event_id)
    save_dir = db.get_setting("save_dir", "")
    active_school = db.get_setting("active_school", "")
    return {
        "event_name": event_name,
        "event_id": event_id,
        "save_dir": save_dir,
        "host_ip": get_local_ip(),
        "port": _port(),
        "count": db.count_resumes(),
        "active_school": active_school,
        "updated_at": db.get_setting("updated_at", ""),
    }


def _port() -> int:
    """从 .env / 环境变量读取端口。"""
    import os

    return int(os.environ.get("PORT", "8000").strip() or "8000")


@router.post("/api/config")
def update_config(payload: ConfigPayload):
    """设置招聘会名称、保存目录、开始收集时间。"""
    if payload.event_name:
        db.set_setting("event_name", payload.event_name)
    if payload.save_dir:
        path = Path(payload.save_dir)
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            raise HTTPException(400, f"无法创建保存目录：{exc}")
        db.set_setting("save_dir", str(path.resolve()))
    if payload.started_at:
        db.set_setting("started_at", payload.started_at)
    db.set_setting("updated_at", now_str())
    return get_config()


@router.get("/api/stats")
def get_stats():
    """大屏实时统计：总数 + 最近上传记录。"""
    return {
        "count": db.count_resumes(),
        "recent": db.list_resumes(limit=20),
    }


@router.get("/api/qrcode")
def qr_code(school: str = ""):
    """生成二维码 PNG：指向手机上传页（携带招聘会 event_id 与学校）。

    二维码 URL：http://本机IP:{PORT}/upload?event={event_id}&school={校名}
    school 为空时生成通用码（不带学校，手机端可自选学校）。
    """
    cfg = get_config()
    base = f"http://{cfg['host_ip']}:{cfg['port']}"
    url = f"{base}/upload?event={cfg['event_id']}"
    if school:
        url += f"&school={school}"
    return build_qr(url)


@router.get("/api/schools/{school_id}/qrcode")
def school_qr_code(school_id: int):
    """某个学校的专属二维码。"""
    school = db.get_school(school_id)
    if not school:
        raise HTTPException(404, "学校不存在")
    cfg = get_config()
    base = f"http://{cfg['host_ip']}:{cfg['port']}"
    url = f"{base}/upload?event={cfg['event_id']}&school={school['name']}"
    return build_qr(url)


@router.post("/api/event/reset")
def reset_event():
    """开启一场新招聘会：换新 event_id + 清空统计。"""
    db.set_setting("event_id", gen_event_id())
    db.set_setting("started_at", now_str())
    db.set_setting("updated_at", now_str())
    return get_config()
