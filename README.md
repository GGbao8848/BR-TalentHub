# BR Tech · 招聘会简历收集系统

招聘会现场用电脑大屏展示二维码，求职者手机扫码上传简历，文件直接落盘到本地指定文件夹。**纯局域网本地部署**，无需联网、无需任何外部服务。

前端基于 **Vue 3 + Naive UI**（Vite 构建），后端基于 **FastAPI + SQLite**。

## 快速开始

### 后端（FastAPI）

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # 按需修改 HOST / PORT / SAVE_DIR
.venv/bin/python -m app.main
```

### 前端（Vite + Vue3 + Naive UI）

```bash
cd web
npm install
npm run build        # 产物输出到 web/dist，由后端 FastAPI 托管
```

> 后端启动时会自动托管 `web/dist` 构建产物（`/` 管理端、`/upload` 手机上传页）。
> 开发时可用 `npm run dev` 启动 Vite dev server（已配置代理 `/api` 到后端 `:18540`）。

### 访问地址

- 管理端大屏：<http://localhost:18540>
- 手机上传页：<http://localhost:18540/upload>

手机与电脑需连接**同一个局域网**，扫码即可上传。电脑防火墙需放行对应端口。

## 使用流程

1. **设置招聘会**：填名称、填简历保存目录，点保存
2. **展示二维码**：大屏自动显示二维码（可切换当前学校），手机扫码进入上传页
3. **实时统计**：大屏每 3 秒刷新，显示已收简历数 + 最近上传记录
4. **简历管理**：按学校/岗位/日期段/关键词筛选，查看/下载/删除，批量导出 ZIP
5. **结束收场**：点「开始新一场」换新 event_id（已收文件不删除）

## 技术栈

| 层 | 选型 |
|---|---|
| 后端 | Python + FastAPI + Uvicorn（Routers 模块化 + Pydantic 模型） |
| 前端 | Vue 3 + Naive UI + Vue Router（Vite 构建） |
| 存储 | SQLite（`data/br_talenthub.db`） |
| 文件 | 本地文件系统（按 学校/岗位/文件名 三级目录） |
| 二维码 | qrcode + Pillow（本地生成，无需外网） |
| 部署 | Linux systemd / Windows，双端一键启动 |

## 项目结构

```
BR_ResumeCollect/
├── app/
│   ├── main.py              # 应用入口：路由挂载、静态托管
│   ├── schemas.py           # Pydantic 请求/响应模型
│   ├── database.py          # SQLite 数据层
│   └── routers/             # 模块化 API 路由
│       ├── config.py        # 配置/统计/二维码/event
│       ├── positions.py     # 岗位管理 + Excel 导入
│       ├── schools.py       # 学校管理 + 绑定岗位 + 二维码
│       ├── resumes.py       # 简历上传/列表/删除/导出
│       └── dashboard.py     # 数据看板
├── web/                     # 前端工程（Vite + Vue3 + Naive UI）
│   ├── src/views/           # 管理端5个视图 + 上传页
│   └── dist/                # 构建产物（后端托管）
├── data/                    # SQLite 数据库 + 简历文件
├── requirements.txt
└── .env / .env.example      # 服务配置（HOST/PORT/SAVE_DIR）
```

## 主要 API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET/POST | `/api/config` | 招聘会配置 + 局域网地址 + 统计 |
| GET | `/api/stats` | 实时统计（总数 + 最近上传） |
| GET | `/api/qrcode` | 生成二维码 PNG（可指定学校） |
| GET/POST/PUT/DELETE | `/api/positions*` | 岗位增删改查 + Excel 导入 |
| GET/POST/DELETE | `/api/schools*` | 学校管理、绑定岗位、激活 |
| POST | `/api/resumes/upload` | 手机上传简历（multipart） |
| GET | `/api/resumes` | 简历列表（筛选 + 分页） |
| DELETE | `/api/resumes/{id}` | 删除简历（含磁盘文件） |
| GET | `/api/resumes/export.zip` | 按筛选条件打包下载 ZIP |
| GET | `/api/resumes/{id}/download` | 下载单条简历 |
| GET | `/api/dashboard` | 看板统计（学校/岗位/近14日） |
| POST | `/api/event/reset` | 开始新一场（换 event_id） |

## 现场注意事项

- 手机和电脑必须连同一个局域网，电脑防火墙需放行端口
- 简历数据只存在于本地电脑，不上云、不经过任何第三方服务
- 只允许 PDF / DOC / DOCX，单文件 ≤ 20MB

## 后续规划

- 简历内容智能筛选（AI 解析简历正文，按技能/关键词匹配岗位）
- Excel 导出简历汇总表
- 上传时自动备份到云端（R2），防本地电脑故障丢数据
