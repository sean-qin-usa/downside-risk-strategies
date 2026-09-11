@echo off
cd /d "C:\Users\OWNER\Claude\Projects\GBC Project"
set "PYEXE=python"
if exist "%USERPROFILE%\anaconda3\python.exe" set "PYEXE=%USERPROFILE%\anaconda3\python.exe"
if exist "%USERPROFILE%\Anaconda3\python.exe" set "PYEXE=%USERPROFILE%\Anaconda3\python.exe"
if exist "C:\ProgramData\Anaconda3\python.exe" set "PYEXE=C:\ProgramData\Anaconda3\python.exe"

echo QUEUE2 START %DATE% %TIME% > queue2_master_log.txt

echo [1/3] OOS 2025/26 IQN evaluation >> queue2_master_log.txt
"%PYEXE%" "q2_oos.py" >> queue2_master_log.txt 2>&1
echo [1/3] done %TIME% >> queue2_master_log.txt

echo [2/3] single-name diversified book reconstruction >> queue2_master_log.txt
"%PYEXE%" "q2_names.py" >> queue2_master_log.txt 2>&1
echo [2/3] done %TIME% >> queue2_master_log.txt

echo [3/3] pull ai2 GPU training script + launchers >> queue2_master_log.txt
ssh -o BatchMode=yes -o ConnectTimeout=15 ai2 "cat ~/gbc_pq/gpu_iqn_mh.py" > pulled_gpu_iqn_mh.py 2>>queue2_master_log.txt
ssh -o BatchMode=yes -o ConnectTimeout=15 ai2 "cat ~/gbc_pq/ai2_train_variants.sh; echo ---RELAUNCH---; cat ~/gbc_pq/ai2_relaunch_mh.sh; echo ---SETUP---; cat ~/gbc_pq/ai2_setup_run.sh" > pulled_ai2_scripts.txt 2>>queue2_master_log.txt
echo [3/3] done %TIME% >> queue2_master_log.txt

echo QUEUE2 DONE_ALL %DATE% %TIME% >> queue2_master_log.txt
