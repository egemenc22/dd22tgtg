@echo off
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
py -3 signal_bot.py --once
if errorlevel 1 python signal_bot.py --once
pause
