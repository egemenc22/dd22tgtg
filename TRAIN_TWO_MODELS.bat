@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (set "PYCMD=py -3") else (set "PYCMD=python")
%PYCMD% -m pip install -r requirements_ml.txt
set /p DBPATH=Full path to your historical candles SQLite database: 
%PYCMD% train_two_models.py --db "%DBPATH%"
pause
