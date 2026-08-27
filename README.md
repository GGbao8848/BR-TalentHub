# BR TalentHub · 招聘会简历收集系统

第一版（MVP）：招聘会现场用电脑大屏展示二维码，求职者手机扫码上传简历，文件直接落盘到本地指定文件夹。**纯局域网本地部署**，无需联网、无需任何外部服务。

## 快速开始

双击 `run.bat`，首次运行会自动创建虚拟环境（venv）并安装依赖，然后启动服务。

- 管理端大屏：<http://localhost:8000>
- 手机上传页：<http://localhost:8000/upload>

手机与电脑需连接**同一个局域网**，扫码上方二维码即可上传。电脑防火墙需放行 8000 端口。

## 使用流程

1. **设置招聘会**：填名称、填简历保存目录（如 `D:\招聘会\2026-08-25`），点保存
2. **展示二维码**：大屏自动显示二维码，手机扫码进入上传页
3. **实时统计**：大屏每 3 秒刷新，显示已收简历数 + 最近上传记录
4. **结束收场**：点「结束本场 / 清空计数」开始新一场（已收文件不删除）

## 技术栈

| 层 | 选型 |
|---|---|
| 后端 | Python + FastAPI + Uvicorn |
| 存储 | SQLite（`data/br_talenthub.db`） |
| 文件 | 本地文件系统（保存目录下，自动按时间戳+随机串重命名） |
| 二维码 | qrcode + Pillow（本地生成，无需外网） |
| 前端 | 原生 HTML/JS（零构建，单进程，现场电脑无需装 Node） |
| 部署 | Windows 原生，双击运行 |

## 项目结构

```
BR_ResumeCollect/
├── app/
│   ├── __init__.py
│   ├── main.py        # FastAPI 应用：路由、二维码、上传、配置
│   └── database.py    # SQLite 数据层
├── static/
│   ├── admin.html     # 管理端大屏
│   └── upload.html    # 手机上传页
├── data/              # SQLite 数据库 + 二维码图片（运行时生成）
├── resumes/           # 默认简历保存目录
├── logs/              # 服务日志
├── requirements.txt
├── run.bat            # 一键启动
└── README.md
```

## 主要 API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/config` | 当前招聘会配置 + 局域网地址 + 统计 |
| POST | `/api/config` | 设置招聘会名称 / 保存目录 |
| GET | `/api/stats` | 实时统计（总数 + 最近上传） |
| GET | `/api/qrcode` | 生成二维码 PNG（指向局域网地址） |
| POST | `/api/resumes/upload` | 手机上传简历（multipart） |
| GET | `/api/resumes` | 上传记录列表 |
| GET | `/api/resumes/{id}/download` | 下载原始简历 |
| POST | `/api/event/reset` | 开始新一场（换 event_id + 清计数） |

## 现场注意事项

- 手机和电脑必须连同一个局域网，电脑防火墙需放行 8000 端口
- 简历数据只存在于本地电脑，不上云、不经过任何第三方服务
- 只允许 PDF / DOC / DOCX，单文件 ≤ 20MB

## 后续规划（第二版起）

- 招聘会管理（多场并存、历史记录）
- Excel 导出上传记录
- AI 简历解析（对接 JD / 面试资料，扩展为 BR 招聘数据平台）
