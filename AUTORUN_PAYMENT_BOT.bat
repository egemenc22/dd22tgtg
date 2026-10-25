@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
if exist "CREDENTIALS.cmd" call "CREDENTIALS.cmd"
if not defined TELEGRAM_VIP_CHAT_ID set "TELEGRAM_VIP_CHAT_ID=-1004409446943"
if not defined TELEGRAM_BOT_TOKEN exit /b 1
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (set "PYCMD=py -3") else (set "PYCMD=python")
%PYCMD% -c "import matplotlib, websocket, numpy, sklearn, joblib" >nul 2>&1
if errorlevel 1 %PYCMD% -m pip install -r requirements.txt >> payment_bot.log 2>&1
:restart
%PYCMD% payment_bot.py >> payment_bot.log 2>&1
timeout /t 15 /nobreak >nul
goto restart
