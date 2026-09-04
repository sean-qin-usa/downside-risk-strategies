@echo off
echo === unstick auto-runner %date% %time% === > "C:\Users\OWNER\Claude\Projects\GBC Project\unblock_marker.txt"
taskkill /F /IM ping.exe 2>nul
taskkill /F /IM schtasks.exe 2>nul
echo killed ping/schtasks >> "C:\Users\OWNER\Claude\Projects\GBC Project\unblock_marker.txt"
echo If autojobs\_heartbeat.txt is still frozen after ~30s, CLOSE the auto-runner window and double-click auto_runner.bat again to restart it. >> "C:\Users\OWNER\Claude\Projects\GBC Project\unblock_marker.txt"
echo done - you can close this window
