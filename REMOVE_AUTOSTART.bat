@echo off
setlocal
set "EGONIA_SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\EGONIA VIP Payment Bot.lnk"
if exist "%EGONIA_SHORTCUT%" del "%EGONIA_SHORTCUT%"
echo Otomatik baslatma kaldirildi. Calisan pencereyi kapatarak mevcut botu durdurabilirsiniz.
pause
