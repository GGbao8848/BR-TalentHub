@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ==========================================
echo   BR TalentHub - 招聘会简历收集系统
echo   (P2P 直传模式：文件不经过任何服务器)
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
echo 使用方式:
echo   1. 打开管理端，设置招聘会与保存目录
echo   2. 大屏显示二维码，手机扫码直传
echo   3. 简历通过 WebRTC 点对点直传电脑，不经过服务器
echo.
echo 按 Ctrl+C 停止服务
echo.
".venv\Scripts\python.exe" -m app.main

pause
