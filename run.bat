@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ==========================================
echo   BR TalentHub - 招聘会简历收集系统
echo ==========================================
echo.

REM 首次运行自动创建虚拟环境并安装依赖
if not exist ".venv\Scripts\python.exe" (
    echo [首次运行] 正在创建虚拟环境...
    python -m venv .venv
    echo [首次运行] 正在安装依赖...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

echo 正在启动服务...
echo 管理端大屏:  http://localhost:8000
echo 手机上传页:  http://localhost:8000/upload
echo.
echo 请确保手机与电脑连接同一局域网，扫码访问
echo 按 Ctrl+C 停止服务
echo.
".venv\Scripts\python.exe" -m app.main

pause
