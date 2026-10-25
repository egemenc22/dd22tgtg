@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
if exist "CREDENTIALS.cmd" call "CREDENTIALS.cmd"
if not defined TELEGRAM_VIP_CHAT_ID set "TELEGRAM_VIP_CHAT_ID=-1004409446943"
if not defined TELEGRAM_BOT_TOKEN (
  echo TELEGRAM_BOT_TOKEN bulunamadi. Mevcut CREDENTIALS.cmd dosyanizi bu klasore koyun.
  pause
  exit /b 1
)
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (set "PYCMD=py -3") else (set "PYCMD=python")
echo EGONIA VIP odeme botu baslatiliyor...
%PYCMD% payment_bot.py
if errorlevel 1 echo HATA: Odeme botu durdu. Yukaridaki mesaji kontrol edin.
pause
