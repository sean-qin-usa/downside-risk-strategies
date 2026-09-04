@echo off
REM One-shot: deploy + schedule the live paper pipeline on ai2 (always-on box).
REM Requires the existing passwordless ssh to steveqin@ai2. All output -> live_paper\ai2_setup_log.txt
cd /d "C:\Users\OWNER\Claude\Projects\GBC Project"
set SSHOPT=-o BatchMode=yes -o StrictHostKeyChecking=accept-new
(
  echo ==== AI2 SETUP %date% %time% ====
  ssh %SSHOPT% steveqin@ai2 "mkdir -p ~/gbc_live/live_paper ~/gbc_live/forward_signals"
  scp %SSHOPT% -q "live_paper\live_signal.py" "live_paper\settle_tickets.py" steveqin@ai2:~/gbc_live/live_paper/
  scp %SSHOPT% -q "live_paper\deploy_ai2\run_live_paper.sh" "live_paper\deploy_ai2\setup_remote.sh" steveqin@ai2:~/gbc_live/
  scp %SSHOPT% -q forward_signals\live_* steveqin@ai2:~/gbc_live/forward_signals/
  ssh %SSHOPT% steveqin@ai2 "sed -i 's/\r$//' ~/gbc_live/run_live_paper.sh ~/gbc_live/setup_remote.sh && bash ~/gbc_live/setup_remote.sh"
  echo FIN_AI2_SETUP
) > "live_paper\ai2_setup_log.txt" 2>&1
