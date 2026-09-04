@echo off
REM Move both daily runs from 9:20 (pre-open, stale quotes) to 9:50 AM ET (post-open + delay buffer).
cd /d "C:\Users\OWNER\Claude\Projects\GBC Project"
(
  echo ==== FIX TIMES %date% %time% ====
  schtasks /create /f /tn "GBC_LivePaperCheck" /tr "\"C:\Users\OWNER\Claude\Projects\GBC Project\run_live_paper.bat\"" /sc weekly /d MON,TUE,WED,THU,FRI /st 09:50
  schtasks /query /tn "GBC_LivePaperCheck"
  ssh -o BatchMode=yes steveqin@ai2 "(crontab -l | grep -v run_live_paper.sh; echo '50 9 * * 1-5 /home/steveqin/gbc_live/run_live_paper.sh') | crontab - && crontab -l | grep run_live_paper"
  echo FIN_FIX
) > "live_paper\fix_times_log2.txt" 2>&1
