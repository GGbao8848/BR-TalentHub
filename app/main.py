"""BR TalentHub P2P 版 —— 招聘会现场简历收集系统（WebRTC 直传）。

架构（关键区别：文件不经过服务器）：
  手机 ──(WebRTC DataChannel 文件直传)──> 电脑浏览器 ──(本地 HTTP 落盘)──> 指定文件夹

  FastAPI 只做"信令"中转（SDP offer/answer、ICE candidate），
  简历文件的二进制数据全程在手机↔电脑两个浏览器之间 P2P 直传，
  不经过 FastAPI、不经过任何云服务器。
"""
import re
import socket
import uuid
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import database as db

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
DEFAULT_DIR = DATA_DIR / "resumes"

app = FastAPI(title="BR TalentHub P2P", version="2.0.0")

# 局域网现场部署，放开跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

ALLOWED_EXT = {".pdf", ".doc", ".docx"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # P2P 直传，放宽到 100MB

db.init_db()


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def gen_event_id() -> str:
    return uuid.uuid4().hex[:6].upper()


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


# ------------------------------------------------------------------ 配置

@app.get("/api/config")
def get_config():
    event_name = db.get_setting("event_name", "BR 招聘会")
    event_id = db.get_setting("event_id", gen_event_id())
    if not db.get_setting("event_id"):
        db.set_setting("event_id", event_id)
    save_dir = db.get_setting("save_dir", str(DEFAULT_DIR))
    return {
        "event_name": event_name,
        "event_id": event_id,
        "save_dir": save_dir,
        "count": db.count_resumes(),
    }


@app.post("/api/config")
def update_config(payload: dict):
    event_name = (payload.get("event_name") or "").strip()
    save_dir = (payload.get("save_dir") or "").strip()
    if event_name:
        db.set_setting("event_name", event_name)
    if save_dir:
        path = Path(save_dir)
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            raise HTTPException(400, f"无法创建保存目录：{exc}")
        db.set_setting("save_dir", str(path.resolve()))
    db.set_setting("updated_at", now_str())
    return get_config()


@app.get("/api/stats")
def get_stats():
    return {"count": db.count_resumes(), "recent": db.list_resumes(limit=20)}


@app.get("/api/qrcode")
def qr_code():
    """生成二维码 PNG：指向手机上传页（局域网 IP 完整地址，P2P 直传无需公网）。"""
    import qrcode
    from io import BytesIO
    from fastapi.responses import Response
    ip = get_local_ip()
    url = f"http://{ip}:8000/upload"
    qr = qrcode.QRCode(border=2, box_size=10, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


# ------------------------------------------------------------------ 信令（内存中转，只传 SDP/ICE，不传文件数据）

# 每场接收会话一个 slot：电脑端登记 offer，手机端取 offer 回 answer
signaling = {
    "offer": None,
    "answer": None,
    "pc_ice": [],   # 电脑端 ICE candidates
    "phone_ice": [],  # 手机端 ICE candidates
}


@app.post("/api/signaling/offer")
def put_offer(payload: dict):
    """电脑端（接收方）登记自己的 SDP offer，并清空上一轮状态。"""
    signaling["offer"] = payload.get("sdp", "")
    signaling["answer"] = None
    signaling["pc_ice"] = []
    signaling["phone_ice"] = []
    return {"ok": True}


@app.get("/api/signaling/offer")
def get_offer():
    """手机端（发送方）取 offer。没有则 404。"""
    if not signaling["offer"]:
        raise HTTPException(404, "暂无连接信息，请确认电脑端已打开")
    return {"sdp": signaling["offer"]}


@app.post("/api/signaling/answer")
def put_answer(payload: dict):
    """手机端回填 answer。"""
    signaling["answer"] = payload.get("sdp", "")
    return {"ok": True}


@app.get("/api/signaling/answer")
def get_answer():
    """电脑端轮询拿 answer。"""
    if not signaling["answer"]:
        raise HTTPException(404, "等待手机端连接")
    return {"sdp": signaling["answer"]}


@app.post("/api/signaling/pc-ice")
def put_pc_ice(payload: dict):
    signaling["pc_ice"].append(payload.get("candidate", ""))
    return {"ok": True}


@app.get("/api/signaling/pc-ice")
def get_pc_ice():
    return {"candidates": signaling["pc_ice"]}


@app.post("/api/signaling/phone-ice")
def put_phone_ice(payload: dict):
    signaling["phone_ice"].append(payload.get("candidate", ""))
    return {"ok": True}


@app.get("/api/signaling/phone-ice")
def get_phone_ice():
    return {"candidates": signaling["phone_ice"]}


@app.post("/api/signaling/reset")
def reset_signaling():
    signaling.update({"offer": None, "answer": None, "pc_ice": [], "phone_ice": []})
    return {"ok": True}


# ------------------------------------------------------------------ 文件接收（电脑浏览器收完 DataChannel 后本地落盘）

@app.post("/api/resumes/save")
async def save_resume(payload: dict):
    """电脑浏览器从 WebRTC DataChannel 收到完整文件字节后，调本接口落盘。

    文件数据实际上从手机 P2P 直传到电脑浏览器，这里只负责写本地磁盘。
    """
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(400, "请填写姓名")
    original = (payload.get("filename") or "resume").strip()
    data = payload.get("data", "")

    import base64
    try:
        content = base64.b64decode(data)
    except Exception:
        raise HTTPException(400, "文件数据解析失败")

    ext = Path(original).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, "仅支持 PDF / DOC / DOCX 格式")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "文件超过 100MB 上限")

    save_dir = Path(db.get_setting("save_dir", str(DEFAULT_DIR)))
    save_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    stored_name = f"{ts}_{uuid.uuid4().hex[:6]}{ext}"
    filepath = save_dir / stored_name
    filepath.write_bytes(content)

    record = {
        "name": name,
        "phone": (payload.get("phone") or "").strip(),
        "position": (payload.get("position") or "").strip(),
        "original": re.sub(r'[\\/:*?"<>|\r\n]', "_", original),
        "filename": stored_name,
        "filepath": str(filepath),
        "filesize": len(content),
        "upload_time": now_str(),
        "ip": "P2P",
    }
    resume_id = db.add_resume(record)
    return {"id": resume_id, "message": "已保存", "filename": original, "bytes": len(content)}


@app.get("/api/resumes")
def list_resumes(limit: int = 50):
    return db.list_resumes(limit=limit)


# ------------------------------------------------------------------ 页面

@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "admin.html")


@app.get("/admin")
def admin():
    return FileResponse(STATIC_DIR / "admin.html")


@app.get("/upload")
def upload_page():
    return FileResponse(STATIC_DIR / "upload.html")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
