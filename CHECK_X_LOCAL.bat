@echo off
cd /d "%~dp0"
py -3 check_x_local.py
if errorlevel 1 python check_x_local.py
pause
