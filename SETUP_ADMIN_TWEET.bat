@echo off
setlocal
cd /d "%~dp0"
if exist "CREDENTIALS.cmd" call "CREDENTIALS.cmd"
py -3 setup_admin_tweet.py
pause
