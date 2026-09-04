@echo off
REM One-time setup: registers a Windows Task Scheduler job that runs the live paper pipeline
REM every weekday at 9:20 AM local (after the open, so delayed quotes are live).
REM The script itself decides which books fire (weekly=Mondays, monthly/xasset=first run of month).
schtasks /create /f /tn "GBC_LivePaperCheck" /tr "\"C:\Users\OWNER\Claude\Projects\GBC Project\run_live_paper.bat\"" /sc weekly /d MON,TUE,WED,THU,FRI /st 09:20 > "C:\Users\OWNER\Claude\Projects\GBC Project\live_paper\setup_schedule_log.txt" 2>&1
schtasks /query /tn "GBC_LivePaperCheck" >> "C:\Users\OWNER\Claude\Projects\GBC Project\live_paper\setup_schedule_log.txt" 2>&1
