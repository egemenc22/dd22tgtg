@echo off
cd /d "%~dp0"
chcp 65001 >nul
if exist "CREDENTIALS.cmd" call "CREDENTIALS.cmd"
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (set "PYCMD=py -3") else (set "PYCMD=python")
%PYCMD% signal_bot.py --check-publishing
pause
