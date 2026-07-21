@echo off
cd /d "C:\Users\OWNER\Claude\Projects\GBC Project"
ssh -o BatchMode=yes -o ConnectTimeout=15 ai2 "echo ===DONEFLAG===; cat ~/gbc_pq/frozen_done.txt 2>/dev/null; echo ===PROC===; pgrep -af gpu_iqn_frozen; echo ===C2019LOG===; tail -6 ~/gbc_pq/frozen_c2019.log 2>/dev/null; echo ===C2024LOG===; tail -6 ~/gbc_pq/frozen_c2024.log 2>/dev/null; echo ===FILES===; ls -la ~/gbc_pq/mh_quantiles_frozen_*.csv 2>/dev/null" > frozen_status.txt 2>&1
scp -o BatchMode=yes ai2:gbc_pq/mh_quantiles_frozen_c2019.csv . >> frozen_status.txt 2>&1
scp -o BatchMode=yes ai2:gbc_pq/mh_quantiles_frozen_c2024.csv . >> frozen_status.txt 2>&1
echo FETCH_ATTEMPT_DONE >> frozen_status.txt
