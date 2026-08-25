# BR TalentHub · 招聘会简历收集系统

**两个分支，两种部署模式：**

| 分支 | 模式 | 特点 |
|---|---|---|
| **`p2p`**（本分支） | WebRTC P2P 直传 | 手机 ↔ 电脑浏览器点对点直传，**文件不经过任何服务器**，可离线，隐私最好 |
| **`cloudflare`** | HTTP + Cloudflare 隧道 | 手机 → Cloudflare → 电脑，公网可访问，简历仍落本地 |

切换到另一分支：`git checkout cloudflare`

---

## P2P 模式（本分支）

**Windows 电脑 + 手机浏览器 + 二维码 + WebRTC P2P + 本地文件夹**

### 架构

```
招聘会电脑（管理端大屏）
      │  生成二维码
      ▼
   手机扫码
      │
      ▼
手机浏览器 ──(WebRTC DataChannel 文件直传)──► 电脑浏览器
                                                    │ 本地落盘
                                                    ▼
                                          D:\招聘会\2026-08\张三_简历.pdf
```

- **简历文件数据**：手机 → 电脑浏览器，**P2P 直传，不经过任何服务器/云**
- **FastAPI 只做信令**（交换 SDP offer/answer 和 ICE candidate，几 KB，不碰文件）
- **完全可离线**：不需要互联网、不需要 Cloudflare、不需要公网 IP
- 类似"面对面快传"（AirDrop / LocalSend 体验）

### 快速开始

双击 `run.bat`（首次自动建 venv 装依赖）：

```
管理端大屏:  http://localhost:8000
手机上传页:  http://localhost:8000/upload
```

1. 管理端设置招聘会名称、保存目录
2. 大屏显示二维码，手机扫码
3. 手机填姓名/岗位，选简历 → 点「直传简历」
4. 简历通过 WebRTC 点对点直传电脑，自动落盘到指定文件夹
5. 大屏实时显示连接数、传输进度、已收简历

### 文件落盘规则

保存目录下自动重命名：`时间戳_随机串.pdf`（如 `20260825173000_a1b2c3.pdf`），SQLite 记录姓名/岗位/原始文件名/大小。

### 项目结构

```
BR_ResumeCollect/
├── app/
│   ├── main.py        # FastAPI：信令接口 + 文件接收落盘 + 配置
│   └── database.py    # SQLite 数据层
├── static/
│   ├── admin.html     # 电脑端大屏（WebRTC 接收方）
│   └── upload.html    # 手机端发送页（WebRTC 发送方）
├── data/              # SQLite 数据库
├── resumes/           # 默认简历保存目录
├── requirements.txt
├── run.bat            # 一键启动
└── README.md
```

### 信令 API（文件不经过这些接口，仅交换连接信息）

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/signaling/offer` | 电脑端登记 SDP offer |
| GET | `/api/signaling/offer` | 手机端取 offer |
| POST | `/api/signaling/answer` | 手机端回填 answer |
| GET | `/api/signaling/answer` | 电脑端轮询 answer |
| POST/GET | `/api/signaling/pc-ice` | 电脑端 ICE candidate |
| POST/GET | `/api/signaling/phone-ice` | 手机端 ICE candidate |
| POST | `/api/resumes/save` | 电脑浏览器收完文件后本地落盘 |

### 现场注意事项

- 手机与电脑需在同一局域网（或可互相访问的网络），供加载页面 + 信令
- **简历文件本身 P2P 直传**，不依赖现场外网质量
- 支持 PDF / DOC / DOCX，≤100MB
- 当前信令为单会话（一台手机同时连接）；多人场景是后续迭代项

### 后续规划

- [ ] 打包成 `BR-TalentHub.exe`（双击启动，免装 Python）
- [ ] 多手机同时连接（会话 ID 区分）
- [ ] 传输断点续传 / 校验
- [ ] Excel 导出、AI 简历解析
