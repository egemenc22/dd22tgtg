@echo off
setlocal
cd /d "%~dp0"
if not exist "CREDENTIALS.cmd" (
  echo Once SETUP_TELEGRAM.bat dosyasini calistirin.
  pause
  exit /b 1
)
set "EGONIA_AUTORUN=%~dp0AUTORUN_PAYMENT_BOT.bat"
set "EGONIA_SCANNER=%~dp0AUTORUN_SCANNER.bat"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$w=New-Object -ComObject WScript.Shell; $d=[Environment]::GetFolderPath('Startup'); $s=$w.CreateShortcut($d+'\EGONIA VIP Payment Bot.lnk'); $s.TargetPath=$env:EGONIA_AUTORUN; $s.WorkingDirectory='%~dp0'; $s.WindowStyle=7; $s.Save(); $r=$w.CreateShortcut($d+'\EGONIA Signal Scanner.lnk'); $r.TargetPath=$env:EGONIA_SCANNER; $r.WorkingDirectory='%~dp0'; $r.WindowStyle=7; $r.Save()"
if errorlevel 1 (
  echo Otomatik baslatma kurulumu basarisiz.
  pause
  exit /b 1
)
start "EGONIA VIP Payment Bot" /min "%~dp0AUTORUN_PAYMENT_BOT.bat"
start "EGONIA Signal Scanner" /min "%~dp0AUTORUN_SCANNER.bat"
echo Kurulum tamamlandi. Odeme botu ve sinyal tarayici simdi ve her Windows acilisinda otomatik calisacak.
echo Odeme logu: %~dp0payment_bot.log
echo Tarayici logu: %~dp0scanner.log
pause
