@echo off
REM One-time setup: registers a Windows Task Scheduler job that runs the full
REM option-chain archive every weekday at 5:30 PM local (after the close, so the
REM day's final delayed quotes/OI are captured). This job is heavy and long-running;
REM keeping it after the close keeps it off the morning trading-signal critical path.
schtasks /create /f /tn "GBC_ChainArchive" /tr "\"C:\Users\OWNER\Claude\Projects\GBC Project\run_chain_archive.bat\"" /sc weekly /d MON,TUE,WED,THU,FRI /st 17:30 > "C:\Users\OWNER\Claude\Projects\GBC Project\live_paper\setup_chain_archive_log.txt" 2>&1
schtasks /query /tn "GBC_ChainArchive" >> "C:\Users\OWNER\Claude\Projects\GBC Project\live_paper\setup_chain_archive_log.txt" 2>&1
echo Registered GBC_ChainArchive (weekdays 17:30). Edit run_chain_archive.bat to set your Drive mirror path.
