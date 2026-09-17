@echo off
title TravelTrip eSIM Production Server
echo ===================================================
echo   TravelTrip World - eSIM Production Backend Server
echo ===================================================
cd /d "%~dp0"
python server.py
pause
