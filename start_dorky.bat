@echo off
title DORKY Launcher

:: Enable UTF-8 code page on Windows console for proper banner rendering
chcp 65001 >nul

:: Automatically navigate to the directory where this .bat script is located
cd /d "%~dp0"

:: Verify the existence of the virtual environment
if not exist "venv\Scripts\python.exe" (
    echo [!] Error: Virtual environment 'venv' not found!
    echo [!] Make sure to run this file from the project root directory.
    pause
    exit /b 1
)

:: Run dorky.py script using Python from venv with forced UTF-8 encoding
.\venv\Scripts\python.exe -X utf8 dorky.py

:: Pause at exit to prevent closing window immediately on double-click
pause
