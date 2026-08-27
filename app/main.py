"""BR Tech 招聘会简历收集系统 —— FastAPI 后端（应用入口）。

第二版：
- 岗位管理：增删 + Excel 导入（识别"岗位名称/岗位要求"表头）
- 学校管理：多校并存，每校独立二维码，绑定岗位
- 简历按 学校/岗位/文件名 三级目录存储
- 数据看板：按学校/岗位/日期多维度统计
- 前端：Vite + Vue3 + Naive UI（构建产物在 web/dist，由本服务托管）
"""
import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import database as db
from app.routers import config as config_router
from app.routers import dashboard as dashboard_router
from app.routers import positions as positions_router
from app.routers import resumes as resumes_router
from app.routers import schools as schools_router

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "web" / "dist"
DATA_DIR = BASE_DIR / "data"

# 加载项目根目录的 .env（HOST/PORT/SAVE_DIR 等配置）
load_dotenv(BASE_DIR / ".env")

# 监听地址与端口：从 .env 或环境变量读取（保证管理页/二维码链接一致）
HOST = os.environ.get("HOST", "0.0.0.0").strip() or "0.0.0.0"
PORT = int(os.environ.get("PORT", "8000").strip() or "8000")

app = FastAPI(title="BR Tech", version="2.0.0")

# 应用启动时确保数据表存在
db.init_db()

# 局域网现场部署，放开跨域让手机端任何来源都可访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------- API 路由

app.include_router(config_router.router)
app.include_router(positions_router.router)
app.include_router(schools_router.router)
app.include_router(resumes_router.router)
app.include_router(dashboard_router.router)

# ---------------------------------------------------------------- 前端页面

if DIST_DIR.exists():
    # Vite 构建产物：静态资源 / 管理端 SPA / 上传页
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

    @app.get("/")
    def index():
        return FileResponse(DIST_DIR / "index.html")

    @app.get("/admin")
    def admin():
        return FileResponse(DIST_DIR / "index.html")

    @app.get("/upload")
    def upload_page():
        return FileResponse(DIST_DIR / "upload.html")
else:
    # 未构建时给出提示
    from fastapi.responses import PlainTextResponse

    @app.get("/")
    def index():
        return PlainTextResponse("前端未构建：请先在 web/ 目录执行 npm run build")

    @app.get("/admin")
    def admin():
        return PlainTextResponse("前端未构建：请先在 web/ 目录执行 npm run build")

    @app.get("/upload")
    def upload_page():
        return PlainTextResponse("前端未构建：请先在 web/ 目录执行 npm run build")


if __name__ == "__main__":
    db.init_db()
    uvicorn.run(app, host=HOST, port=PORT)
