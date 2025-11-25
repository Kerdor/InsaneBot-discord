@echo off
setlocal enabledelayedexpansion

:: Set Python executable path (update this if Python is not in PATH)
set PYTHON=python

:: Set the path to your config.py directory
set CONFIG_PATH=%~dp0config.py

:: Run the bot
%PYTHON% "%~dp0main.py"

:: Keep the window open if there's an error
if errorlevel 1 (
    echo.
    echo Bot has stopped with an error. Press any key to exit...
    pause >nul
)
