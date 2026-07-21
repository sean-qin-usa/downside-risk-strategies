@echo off
set G=C:\Users\OWNER\Claude\Projects\GBC Project
scp -o BatchMode=yes "%G%\misspec_frontier.py" steveqin@ai2:~/sean_dev/GBC_data/
ssh -o BatchMode=yes steveqin@ai2 "cd ~/sean_dev/GBC_data && python3 misspec_frontier.py > misspec_frontier_log.txt 2>&1; echo RC=$?"
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/misspec_frontier_results.json "%G%\misspec_frontier_results.json"
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/misspec_frontier_log.txt "%G%\misspec_frontier_log.txt"
