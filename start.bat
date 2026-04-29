@echo off
setlocal
title LLM Orchestrator Dashboard

set APP_HOST=0.0.0.0
set APP_PORT=8000
set APP_URL=http://127.0.0.1:%APP_PORT%

echo === LLM Orchestrator Dashboard ===
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+ first.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo Created .env from .env.example
    ) else (
        echo [WARN] .env.example not found. Running without .env.
    )
)

if not exist ".venv\.deps_installed" (
    echo Installing dependencies...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
    echo ok > ".venv\.deps_installed"
) else (
    echo Dependencies already installed.
)

echo.
echo Checking runtime mode...
findstr /C:"OPENAI_API_KEY=your-openai-compatible-key" ".env" >nul 2>nul
if errorlevel 1 (
    echo Mode: Real API mode if valid API keys are configured.
) else (
    echo Mode: Mock mode. Edit .env to enable real model calls.
)

echo.
echo Starting server at %APP_URL%
echo Press Ctrl+C to stop.
echo.

start "" "%APP_URL%"
uvicorn app.main:app --host %APP_HOST% --port %APP_PORT% --reload

echo.
echo Server stopped.
pause
