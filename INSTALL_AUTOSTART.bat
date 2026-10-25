@echo off
setlocal
cd /d "%~dp0"
if not exist "CREDENTIALS.cmd" (
  echo Once SETUP_TELEGRAM.bat dosyasini calistirin.
  pause
  exit /b 1
)
set "EGONIA_AUTORUN=%~dp0AUTORUN_PAYMENT_BOT.bat"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut([Environment]::GetFolderPath('Startup')+'\EGONIA VIP Payment Bot.lnk'); $s.TargetPath=$env:EGONIA_AUTORUN; $s.WorkingDirectory='%~dp0'; $s.WindowStyle=7; $s.Save()"
if errorlevel 1 (
  echo Otomatik baslatma kurulumu basarisiz.
  pause
  exit /b 1
)
start "EGONIA VIP Payment Bot" /min "%~dp0AUTORUN_PAYMENT_BOT.bat"
echo Kurulum tamamlandi. Odeme botu simdi ve her Windows acilisinda otomatik calisacak.
echo Log: %~dp0payment_bot.log
pause
