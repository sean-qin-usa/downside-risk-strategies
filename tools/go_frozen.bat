@echo off
cd /d "C:\Users\OWNER\Claude\Projects\GBC Project"
set "PYEXE=python"
if exist "%USERPROFILE%\anaconda3\python.exe" set "PYEXE=%USERPROFILE%\anaconda3\python.exe"
if exist "%USERPROFILE%\Anaconda3\python.exe" set "PYEXE=%USERPROFILE%\Anaconda3\python.exe"
if exist "C:\ProgramData\Anaconda3\python.exe" set "PYEXE=C:\ProgramData\Anaconda3\python.exe"

echo FROZEN START %DATE% %TIME% > frozen_master_log.txt

echo [1/3] corrected OOS calibration eval >> frozen_master_log.txt
"%PYEXE%" "q3_oos.py" >> frozen_master_log.txt 2>&1
echo [1/3] done %TIME% >> frozen_master_log.txt

echo [2/3] deploy frozen script to ai2 >> frozen_master_log.txt
scp -o BatchMode=yes -o ConnectTimeout=20 "gpu_iqn_frozen.py" ai2:gbc_pq/ >> frozen_master_log.txt 2>&1
echo [2/3] scp rc=%ERRORLEVEL% %TIME% >> frozen_master_log.txt

echo [3/3] launch frozen retrain (fire-and-forget, two cutoffs) >> frozen_master_log.txt
ssh -o BatchMode=yes -o ConnectTimeout=20 ai2 "cd ~/gbc_pq && nohup bash -c 'export MHPANEL=mh_panel_v2.csv.gz; FROZEN_CUTOFF=2019-12-31 FROZEN_TAG=c2019 /usr/bin/python3 -u gpu_iqn_frozen.py > frozen_c2019.log 2>&1; FROZEN_CUTOFF=2024-12-31 FROZEN_TAG=c2024 /usr/bin/python3 -u gpu_iqn_frozen.py > frozen_c2024.log 2>&1; echo DONE > frozen_done.txt' >/dev/null 2>&1 & echo LAUNCHED_PID $!" >> frozen_master_log.txt 2>&1
echo [3/3] launch issued %TIME% >> frozen_master_log.txt
echo FROZEN DONE %DATE% %TIME% >> frozen_master_log.txt
