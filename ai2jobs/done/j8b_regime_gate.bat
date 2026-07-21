@echo off
set G=C:\Users\OWNER\Claude\Projects\GBC Project
scp -o BatchMode=yes "%G%\regime_gate_eval.py" steveqin@ai2:~/sean_dev/GBC_data/
ssh -o BatchMode=yes steveqin@ai2 "cd ~/sean_dev/GBC_data && rm -f regime_gate_results.json && python3 regime_gate_eval.py > regime_gate_log.txt 2>&1; echo RC=$?"
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/regime_gate_results.json "%G%\regime_gate_results.json"
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/regime_gate_log.txt "%G%\regime_gate_log.txt"
