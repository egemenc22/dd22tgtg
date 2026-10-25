@echo off
setlocal
set "EGONIA_SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\EGONIA VIP Payment Bot.lnk"
set "EGONIA_SCANNER_SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\EGONIA Signal Scanner.lnk"
if exist "%EGONIA_SHORTCUT%" del "%EGONIA_SHORTCUT%"
if exist "%EGONIA_SCANNER_SHORTCUT%" del "%EGONIA_SCANNER_SHORTCUT%"
echo Otomatik baslatma kaldirildi. Calisan pencereyi kapatarak mevcut botu durdurabilirsiniz.
pause
