@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ==========================================
echo   BR TalentHub - 招聘会简历收集系统
echo   (公网模式：Cloudflare 快速隧道)
echo ==========================================
echo.

REM ---- 1. 依赖准备 ----
if not exist ".venv\Scripts\python.exe" (
    echo [首次运行] 正在创建虚拟环境...
    python -m venv .venv
    echo [首次运行] 正在安装依赖...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

REM ---- 2. 检查 cloudflared ----
set CF="C:\Program Files (x86)\cloudflared\cloudflared.exe"
if not exist %CF% set CF="C:\Program Files\cloudflared\cloudflared.exe"
where cloudflared >nul 2>nul
if %errorlevel%==0 (set CF=cloudflared)
if not exist %CF% (
    echo [错误] 未找到 cloudflared，请先安装：
    echo   winget install --id Cloudflare.cloudflared -e
    pause
    exit /b 1
)

REM ---- 3. 启动后端服务（新窗口，日志到 logs\server.log）----
if not exist "logs" mkdir logs
echo [1/3] 启动本地服务 http://localhost:8000 ...
start "BR TalentHub 服务" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

REM 等待服务就绪
echo 等待服务启动...
timeout /t 4 /nobreak >nul

REM ---- 4. 启动快速隧道 ----
echo [2/3] 启动 Cloudflare 快速隧道...
start "BR TalentHub 隧道" cmd /k "%CF% tunnel --url http://localhost:8000 --no-autoupdate --logfile %cd%\logs\tunnel.log"

REM 等待隧道就绪并抓取公网地址
echo 等待公网地址...
set PUBLIC_URL=
for /l %%i in (1,1,20) do (
    timeout /t 1 /nobreak >nul
    for /f "usebackq delims=" %%u in (`findstr /r "https://.*trycloudflare.com" logs\tunnel.log ^| findstr /v "wss"`) do (
        if not defined PUBLIC_URL set PUBLIC_URL=%%u
    )
    if defined PUBLIC_URL goto :goturl
)
echo [警告] 未能自动获取公网地址，请查看 logs\tunnel.log 手动复制。
goto :manual

:goturl
echo.
echo [3/3] 公网地址：%PUBLIC_URL%
echo.
REM 写入后端配置，让二维码指向公网地址（用 urllib，无额外依赖）
".venv\Scripts\python.exe" -c "import urllib.request as u, sys; req=u.Request('http://localhost:8000/api/config', data=('{\"public_url\":\"%PUBLIC_URL%\"}').encode(), headers={'Content-Type':'application/json'}, method='POST'); u.urlopen(req, timeout=5)" >nul 2>nul
echo 已写入配置，二维码将指向公网地址。

:manual
echo.
echo ==========================================
echo   管理端大屏:  http://localhost:8000
echo   手机上传页:  扫码上方二维码（公网可访问）
echo   停止服务:    关闭两个新开的窗口
echo ==========================================
echo.
pause
