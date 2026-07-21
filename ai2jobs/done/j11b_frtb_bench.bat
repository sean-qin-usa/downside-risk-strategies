@echo off
set G=C:\Users\OWNER\Claude\Projects\GBC Project
scp -o BatchMode=yes "%G%\frtb_bench.py" steveqin@ai2:~/sean_dev/GBC_data/
ssh -o BatchMode=yes steveqin@ai2 "cd ~/sean_dev/GBC_data && python3 frtb_bench.py > frtb_bench_log.txt 2>&1; echo RC=$?"
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/frtb_bench_results.json "%G%\frtb_bench_results.json"
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/frtb_bench_log.txt "%G%\frtb_bench_log.txt"
