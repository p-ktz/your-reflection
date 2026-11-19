@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-windows.ps1" %*
set "result=%ERRORLEVEL%"
echo.
if not "%result%"=="0" echo Startup failed. Read the error above.
echo Press any key to close this window.
pause >nul
exit /b %result%
