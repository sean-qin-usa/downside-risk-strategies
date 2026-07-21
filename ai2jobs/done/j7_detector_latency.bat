@echo off
set G=C:\Users\OWNER\Claude\Projects\GBC Project
scp -o BatchMode=yes "%G%\detector_latency.py" steveqin@ai2:~/sean_dev/GBC_data/
ssh -o BatchMode=yes steveqin@ai2 "cd ~/sean_dev/GBC_data && python3 detector_latency.py > detector_latency_log.txt 2>&1; echo RC=$?"
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/detector_latency_results.json "%G%\detector_latency_results.json"
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/detector_latency_log.txt "%G%\detector_latency_log.txt"
