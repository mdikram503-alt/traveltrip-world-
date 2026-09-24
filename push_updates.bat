@echo off
echo ========================================================
echo  TravelTrip World - Pushing Live Updates to GitHub & Vercel
echo ========================================================
cd /d "%~dp0"

set "GIT_EXE="
for /d %%i in ("%LOCALAPPDATA%\GitHubDesktop\app-*") do (
    if exist "%%i\resources\app\git\cmd\git.exe" set "GIT_EXE=%%i\resources\app\git\cmd\git.exe"
)
if not defined GIT_EXE (
    if exist "C:\Program Files\Git\cmd\git.exe" set "GIT_EXE=C:\Program Files\Git\cmd\git.exe"
)
if not defined GIT_EXE (
    if exist "C:\Program Files\Git\bin\git.exe" set "GIT_EXE=C:\Program Files\Git\bin\git.exe"
)
if not defined GIT_EXE (
    set "GIT_EXE=git"
)

echo Using Git: %GIT_EXE%
"%GIT_EXE%" add .
"%GIT_EXE%" commit -m "Fix login, logout, forgot password, and eSIM persistence in localStorage"
"%GIT_EXE%" push origin main

echo ========================================================
echo  SUCCESS: Code pushed to GitHub! Vercel is auto-deploying.
echo ========================================================
