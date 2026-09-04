@echo off
rem Run this (double-click) once ai2 training finishes (train_k5.log ends with "DONE").
rem It fetches the K=5 quantiles; then the same-rows comparison is a cheap sandbox merge onto samerows_merged.csv (GARCH cols already there).
echo === train_k5 progress ===
ssh -o BatchMode=yes -o ConnectTimeout=20 ai2 "tail -3 ~/gbc_pq/train_k5.log; ls -la ~/gbc_pq/mh_quantiles_k5.csv 2>/dev/null" > "C:\Users\OWNER\Claude\Projects\GBC Project\k5_status.txt" 2>&1
type "C:\Users\OWNER\Claude\Projects\GBC Project\k5_status.txt"
echo === attempting fetch (only succeeds if training done) ===
scp -o BatchMode=yes ai2:~/gbc_pq/mh_quantiles_k5.csv "C:\Users\OWNER\Claude\Projects\GBC Project\mh_quantiles_k5.csv"
echo done
