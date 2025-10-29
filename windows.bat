@echo off

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not found. Installing Python... please do not close this window.
    
    REM Download Python installer for 3.11.4
    curl -o python_installer.exe https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe

    REM Run Python installer
    start /wait python_installer.exe InstallAllUsers=1 PrependPath=1

    REM Remove installer
    del python_installer.exe

    echo Python has been installed.
)


REM Install uv
python -m pip install uv

REM create the venv and activate it
python -m uv venv --clear
call ".venv/bin/activate.bat"

REM sync dependencies
python -m uv sync

REM Run GUI
python -m uv run src/gui/gui_main.py

REM Clean up venv
call ".venv/bin/deactivate.bat"
