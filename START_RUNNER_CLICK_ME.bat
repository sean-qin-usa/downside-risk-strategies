@echo off
rem One-click starter: launches the auto-runner WITHOUT clearing the queued jobs.
start "gbc_auto_runner" /min cmd /c "C:\Users\OWNER\Claude\Projects\GBC Project\auto_runner.bat"
echo Runner launched. This window can be closed.
timeout /t 4 >nul
