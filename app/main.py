"""BR TalentHub 招聘会简历收集系统 —— FastAPI 后端。

第一版 MVP：
- 管理端大屏：设置招聘会/保存目录、展示二维码、实时统计
- 手机端上传：姓名/手机/岗位 + 附件（PDF/DOC/DOCX）
- 数据落 SQLite，文件落本地目录，纯局域网本地部署，无需联网/登录
"""
import os
import re
import socket
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path

import qrcode
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from app import database as db

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"

# 加载项目根目录的 .env（HOST/PORT/SAVE_DIR 等配置）
load_dotenv(BASE_DIR / ".env")

# 监听地址与端口：从 .env 或环境变量读取（保证管理页/二维码链接一致）
HOST = os.environ.get("HOST", "0.0.0.0").strip() or "0.0.0.0"
PORT = int(os.environ.get("PORT", "8000").strip() or "8000")
# 默认简历保存目录（.env 里可覆盖为绝对路径；空值则用项目内默认）
_env_save_dir = os.environ.get("SAVE_DIR", "").strip()
DEFAULT_DIR = Path(_env_save_dir) if _env_save_dir else Path(DATA_DIR / "resumes")

app = FastAPI(title="BR TalentHub", version="1.0.0")

# 应用启动时确保数据表存在
db.init_db()

# 局域网现场部署，放开跨域让手机端任何来源都可访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

ALLOWED_EXT = {".pdf", ".doc", ".docx"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def gen_event_id() -> str:
    """短 ID：给每个招聘会一个唯一标识，二维码里携带。"""
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


# ---------------------------------------------------------------- 配置与招聘会

@app.get("/api/config")
def get_config():
    """管理端/上传页共用：当前招聘会配置 + 局域网地址 + 统计。"""
    event_name = db.get_setting("event_name", "BR 招聘会")
    event_id = db.get_setting("event_id", gen_event_id())
    if not db.get_setting("event_id"):
        db.set_setting("event_id", event_id)
    save_dir = db.get_setting("save_dir", str(DEFAULT_DIR))
    return {
        "event_name": event_name,
        "event_id": event_id,
        "save_dir": save_dir,
        "host_ip": get_local_ip(),
        "port": PORT,
        "count": db.count_resumes(),
        "updated_at": db.get_setting("updated_at", ""),
    }


@app.post("/api/config")
def update_config(payload: dict):
    """设置招聘会名称、保存目录、开始收集时间。"""
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

    if "started_at" in payload:
        db.set_setting("started_at", payload["started_at"])
    db.set_setting("updated_at", now_str())
    return get_config()


@app.get("/api/stats")
def get_stats():
    """大屏实时统计：总数 + 最近上传记录。"""
    return {
        "count": db.count_resumes(),
        "recent": db.list_resumes(limit=20),
    }


@app.get("/api/qrcode")
def qr_code():
    """生成二维码 PNG：指向手机上传页（携带招聘会 event_id）。

    二维码指向局域网地址（http://本机IP:{PORT}/upload?event=...）。
    """
    cfg = get_config()
    base = f"http://{cfg['host_ip']}:{cfg['port']}"
    url = f"{base}/upload?event={cfg['event_id']}"
    qr = qrcode.QRCode(border=2, box_size=10, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@app.post("/api/event/reset")
def reset_event():
    """开启一场新招聘会：换新 event_id + 清空统计。"""
    db.set_setting("event_id", gen_event_id())
    db.set_setting("started_at", now_str())
    db.set_setting("updated_at", now_str())
    return get_config()


# ---------------------------------------------------------------- 简历上传

@app.post("/api/resumes/upload")
async def upload_resume(
    file: UploadFile = File(...),
    name: str = Form(""),
    phone: str = Form(""),
    position: str = Form(""),
):
    """手机端提交简历：校验 → 落盘 → 记录到 SQLite。"""
    name = (name or "").strip()
    phone = (phone or "").strip()
    position = (position or "").strip()
    if not name:
        raise HTTPException(400, "请填写姓名")

    original = file.filename or "resume"
    ext = Path(original).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, "仅支持 PDF / DOC / DOCX 格式")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "文件超过 20MB 上限")

    # 清理文件名里的不安全字符
    safe_original = re.sub(r'[\\/:*?"<>|\r\n]', "_", original)

    save_dir = Path(db.get_setting("save_dir", str(DEFAULT_DIR)))
    save_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    stored_name = f"{ts}_{uuid.uuid4().hex[:6]}{ext}"
    filepath = save_dir / stored_name
    filepath.write_bytes(content)

    record = {
        "name": name,
        "phone": phone,
        "position": position,
        "original": safe_original,
        "filename": stored_name,
        "filepath": str(filepath),
        "filesize": len(content),
        "upload_time": now_str(),
        "ip": "",
    }
    resume_id = db.add_resume(record)
    return {"id": resume_id, "message": "上传成功", "filename": original}


@app.get("/api/resumes")
def list_resumes(limit: int = 50):
    return db.list_resumes(limit=limit)


@app.get("/api/resumes/{resume_id}/download")
def download_resume(resume_id: int):
    row = db.get_resume(resume_id)
    if not row:
        raise HTTPException(404, "记录不存在")
    path = Path(row["filepath"])
    if not path.exists():
        raise HTTPException(404, "文件已丢失")
    return FileResponse(path, filename=row["original"])


# ---------------------------------------------------------------- 页面路由

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
    db.init_db()
    uvicorn.run(app, host=HOST, port=PORT)
