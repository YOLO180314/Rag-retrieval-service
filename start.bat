@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ================================
echo   RAG 检索服务 启动脚本
echo   访问地址: http://localhost:8001
echo   Swagger文档: http://localhost:8001/docs
echo   按 Ctrl+C 停止服务
echo ================================
echo.
".venv\Scripts\python.exe" main.py
pause
