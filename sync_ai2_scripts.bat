@echo off
REM Push the current pipeline scripts to ai2 (run after any script edit).
cd /d "C:\Users\OWNER\Claude\Projects\GBC Project"
(
  echo ==== SYNC %date% %time% ====
  scp -o BatchMode=yes -q "live_paper\live_signal.py" "live_paper\settle_tickets.py" steveqin@ai2:~/gbc_live/live_paper/
  ssh -o BatchMode=yes steveqin@ai2 "ls -la ~/gbc_live/live_paper/*.py"
  echo FIN_SYNC
) > "live_paper\sync_log.txt" 2>&1
