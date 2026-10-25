@echo off
cd /d "%~dp0"
py -3 -m unittest discover -p "test_*.py"
if errorlevel 1 python -m unittest discover -p "test_*.py"
pause
