@echo off
cd /d "%~dp0"
echo Starting Rocket Rally on port 8082...
python scripts\server.py
pause
