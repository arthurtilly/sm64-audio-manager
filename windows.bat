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


REM Install Python dependencies
python -m pip install PyQt6
python -m pip install av

REM Run GUI
python src/gui/gui_main.py
