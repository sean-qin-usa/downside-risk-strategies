@echo off
taskkill /F /IM ssh.exe >nul 2>&1
timeout /t 2 /nobreak >nul
ssh -o BatchMode=yes -o ConnectTimeout=15 ai2 "pgrep -af gpu_iqn_mh; echo ---LOG---; tail -6 ~/gbc_pq/train_camp.log 2>/dev/null" > "C:\Users\OWNER\Claude\Projects\GBC Project\camp_status.txt" 2>&1
echo UNBLOCKED >> "C:\Users\OWNER\Claude\Projects\GBC Project\camp_status.txt"
