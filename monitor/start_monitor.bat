@echo off
title TravelTrip 24/7 VPS Health Monitor Daemon
echo ===================================================
echo   TravelTrip 24/7 Server Health Monitoring Daemon
echo ===================================================
cd /d "%~dp0"
python vps_health_daemon.py
pause
