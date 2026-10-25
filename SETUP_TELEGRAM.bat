@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (set "PYCMD=py -3") else (set "PYCMD=python")
%PYCMD% setup_telegram.py
if errorlevel 1 (
  echo Setup failed. Check token and retry.
  pause
  exit /b 1
)
call CHECK_REMOTE_CONNECTIONS.bat
