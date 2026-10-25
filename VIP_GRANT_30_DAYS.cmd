@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
set /p UID=Telegram numeric user ID (payment confirmed): 
if not defined UID goto :end
py -3 signal_bot.py --members-action grant --user-id %UID% --days 30
:end
pause
