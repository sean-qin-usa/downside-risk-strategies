@echo off
set G=C:\Users\OWNER\Claude\Projects\GBC Project
scp -o BatchMode=yes "%G%\tail_iqn.py" steveqin@ai2:~/sean_dev/GBC_data/
ssh -o BatchMode=yes steveqin@ai2 "cd ~/sean_dev/GBC_data && echo ===GPU=== && nvidia-smi --query-gpu=memory.used,memory.total,memory.free,utilization.gpu --format=csv && echo ===RUN=== && python3 tail_iqn.py > tail_iqn_log.txt 2>&1; echo RC=$?" > "%G%\tail_iqn_gpu_and_rc.txt" 2>&1
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/tail_iqn_results.json "%G%\tail_iqn_results.json"
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/tail_iqn_log.txt "%G%\tail_iqn_log.txt"
