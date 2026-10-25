@echo off
setlocal
cd /d "%~dp0"
if exist "CREDENTIALS.cmd" call "CREDENTIALS.cmd"
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (set "PYCMD=py -3") else (set "PYCMD=python")
%PYCMD% telegram_free_test.py
pause
