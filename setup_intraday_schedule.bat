@echo off
REM One-time setup: registers a Task Scheduler job that snapshots the intraday watchlist
REM every 15 minutes on weekdays from 09:30, for 6h45m (through ~16:15), then stops.
REM The script's own market-hours guard makes off-hours firings no-ops, so this is belt+braces.
schtasks /create /f /tn "GBC_IntradayWatchlist" /tr "\"C:\Users\OWNER\Claude\Projects\GBC Project\run_intraday_watchlist.bat\"" /sc weekly /d MON,TUE,WED,THU,FRI /st 09:30 /ri 15 /du 0006:45 /k > "C:\Users\OWNER\Claude\Projects\GBC Project\live_paper\setup_intraday_log.txt" 2>&1
schtasks /query /tn "GBC_IntradayWatchlist" >> "C:\Users\OWNER\Claude\Projects\GBC Project\live_paper\setup_intraday_log.txt" 2>&1
echo Registered GBC_IntradayWatchlist (weekdays, every 15 min 09:30-16:15).
