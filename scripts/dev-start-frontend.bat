@echo off
chcp 65001 >nul

REM 前端开发环境启动脚本 (Windows)

echo 🎨 启动前端开发环境...

REM 获取脚本所在目录并切换到 frontend 目录
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "FRONTEND_DIR=%PROJECT_DIR%\frontend"

REM 切换到 frontend 目录
cd /d "%FRONTEND_DIR%"

REM 检查是否在 frontend 目录
if not exist package.json (
    echo ❌ 错误: 未找到 frontend 目录或 package.json 文件
    echo 期望位置: %FRONTEND_DIR%
    pause
    exit /b 1
)

REM 检查 Node.js 是否安装
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到 Node.js
    echo 请先安装 Node.js: https://nodejs.org/
    pause
    exit /b 1
)

REM 检查 npm 是否安装
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到 npm
    echo 请确保 Node.js 已正确安装
    pause
    exit /b 1
)

REM 检查 node_modules 是否存在
if not exist node_modules (
    echo 📦 安装依赖...
    npm install
    if %errorlevel% neq 0 (
        echo ❌ 错误: 依赖安装失败
        pause
        exit /b 1
    )
)

REM 检查后端服务是否运行
echo 🔍 检查后端服务...
where curl >nul 2>&1
if %errorlevel% equ 0 (
    curl -s http://localhost:8000/api/v1/utils/health-check/ >nul 2>&1
    if errorlevel 1 (
        echo ⚠️  警告: 后端服务似乎未运行
        echo 请先启动后端服务:
        echo   docker compose up -d db adminer mailcatcher prestart backend
        echo   或运行: docker compose watch
        echo.
    ) else (
        echo ✅ 后端服务运行正常
        echo.
    )
) else (
    echo ℹ️  未找到 curl 命令，跳过后端服务检查
    echo.
)

REM 启动前端开发服务器
echo 🚀 启动前端开发服务器...
echo 前端将在 http://localhost:5173 启动
echo 按 Ctrl+C 停止服务器
echo.

npm run dev
