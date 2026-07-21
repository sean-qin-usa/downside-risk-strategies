@echo off
set G=C:\Users\OWNER\Claude\Projects\GBC Project
echo start %date% %time% > "%G%\ai2_battery_done.txt"
scp -o BatchMode=yes "%G%\industry_bench.py" "%G%\horizon.py" steveqin@ai2:~/sean_dev/GBC_data/ >> "%G%\ai2_battery_done.txt" 2>&1
ssh -o BatchMode=yes steveqin@ai2 "cd ~/sean_dev/GBC_data && python3 industry_bench.py > industry_bench_log.txt 2>&1; echo IB_RC=$?; python3 horizon.py > horizon_log.txt 2>&1; echo HZ_RC=$?" >> "%G%\ai2_battery_done.txt" 2>&1
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/industry_bench_results.json "%G%\industry_bench_results.json" >> "%G%\ai2_battery_done.txt" 2>&1
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/horizon_results.json "%G%\horizon_results.json" >> "%G%\ai2_battery_done.txt" 2>&1
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/industry_bench_log.txt "%G%\industry_bench_log.txt" >> "%G%\ai2_battery_done.txt" 2>&1
echo DONE_BATTERY %date% %time% >> "%G%\ai2_battery_done.txt"
