@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
if exist "CREDENTIALS.cmd" call "CREDENTIALS.cmd"
if not defined TELEGRAM_VIP_CHAT_ID set "TELEGRAM_VIP_CHAT_ID=-1004409446943"
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (set "PYCMD=py -3") else (set "PYCMD=python")
%PYCMD% --version
%PYCMD% -c "import matplotlib, websocket, numpy, sklearn, joblib" >nul 2>&1
if errorlevel 1 (
  echo Installing chart dependency matplotlib...
  %PYCMD% -m pip install -r requirements.txt
  if errorlevel 1 (echo DEPENDENCY INSTALL FAILED & pause & exit /b 1)
)
%PYCMD% auto_bootstrap_models.py
if errorlevel 1 (echo MODEL INITIALIZATION FAILED - check auto_bootstrap.log & pause & exit /b 1)
%PYCMD% signal_bot.py
if errorlevel 1 echo ERROR: See signal_service.log
pause
