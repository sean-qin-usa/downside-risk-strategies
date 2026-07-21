@echo off
rem Clean restart of the auto-runner: clear already-run job files, then start a fresh runner.
set J=C:\Users\OWNER\Claude\Projects\GBC Project\autojobs
if not exist "%J%\done" mkdir "%J%\done"
rem move all already-run job .bat out of the queue so the fresh runner does NOT re-run them
move /y "%J%\*.bat" "%J%\done\" >nul 2>&1
rem also move their .py (optional; leave .py, only .bat drives the runner)
echo cleared queue %date% %time% > "C:\Users\OWNER\Claude\Projects\GBC Project\runner_restart_marker.txt"
rem start a fresh runner in its own window (auto_runner loops autojobs\*.bat)
start "gbc_auto_runner" cmd /c "C:\Users\OWNER\Claude\Projects\GBC Project\auto_runner.bat"
echo RESTARTED - fresh runner started, queue cleared >> "C:\Users\OWNER\Claude\Projects\GBC Project\runner_restart_marker.txt"
echo done
