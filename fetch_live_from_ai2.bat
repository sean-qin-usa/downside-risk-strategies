@echo off
REM Pull the canonical live paper-trade data from ai2 into this folder (mirror for Claude checks).
cd /d "C:\Users\OWNER\Claude\Projects\GBC Project"
scp -q steveqin@ai2:~/gbc_live/forward_signals/* forward_signals/ > "live_paper\fetch_log.txt" 2>&1
scp -q steveqin@ai2:~/gbc_live/live_paper/live_paper_log.txt live_paper\ai2_live_paper_log.txt >> "live_paper\fetch_log.txt" 2>&1
scp -q steveqin@ai2:~/gbc_live/live_paper/quote_snapshots.csv live_paper\ >> "live_paper\fetch_log.txt" 2>&1
echo FIN_FETCH >> "live_paper\fetch_log.txt"
