@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
py -3 signal_bot.py --members-action sync
pause
