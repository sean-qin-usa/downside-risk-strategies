@echo off
set G=C:\Users\OWNER\Claude\Projects\GBC Project
scp -o BatchMode=yes "%G%\gibbs_var_es_v2.py" steveqin@ai2:~/sean_dev/GBC_data/
ssh -o BatchMode=yes steveqin@ai2 "cd ~/sean_dev/GBC_data && python3 gibbs_var_es_v2.py > gibbs_var_es_v2_log.txt 2>&1; echo RC=$?"
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/gibbs_var_es_v2_results.json "%G%\gibbs_var_es_v2_results.json"
scp -o BatchMode=yes steveqin@ai2:~/sean_dev/GBC_data/gibbs_var_es_v2_log.txt "%G%\gibbs_var_es_v2_log.txt"
