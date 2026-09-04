@echo off
cd /d "C:\Users\OWNER\Claude\Projects\GBC Project"
set "PYEXE=python"
if exist "%USERPROFILE%\anaconda3\python.exe" set "PYEXE=%USERPROFILE%\anaconda3\python.exe"
if exist "%USERPROFILE%\Anaconda3\python.exe" set "PYEXE=%USERPROFILE%\Anaconda3\python.exe"
if exist "C:\ProgramData\Anaconda3\python.exe" set "PYEXE=C:\ProgramData\Anaconda3\python.exe"

echo QUEUE START %DATE% %TIME% > queue_master_log.txt

echo [1/4] upgrade pyarrow >> queue_master_log.txt
"%PYEXE%" -m pip install -U "pyarrow>=17" >> queue_master_log.txt 2>&1
echo [1/4] pyarrow done %TIME% >> queue_master_log.txt

echo [2/4] export saved parquet series >> queue_master_log.txt
"%PYEXE%" "q_export.py" >> queue_master_log.txt 2>&1
echo [2/4] export done %TIME% >> queue_master_log.txt

echo [3/4] probe single-name data >> queue_master_log.txt
"%PYEXE%" "q_probe.py" >> queue_master_log.txt 2>&1
echo [3/4] probe done %TIME% >> queue_master_log.txt

echo [4/4] inspect ai2 gpu scripts >> queue_master_log.txt
ssh -o BatchMode=yes -o ConnectTimeout=15 ai2 "echo ===GBC_PQ===; ls -la ~/gbc_pq/ 2>/dev/null; echo ===PYFILES===; ls ~/gbc_pq/*.py ~/gbc_pq/*.sh 2>/dev/null; echo ===HEAD_TRAIN===; for f in ~/gbc_pq/*mh*.py ~/gbc_pq/*iqn*.py; do echo ----$f----; sed -n '1,45p' $f; done 2>/dev/null; echo ===NVIDIA===; nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv 2>/dev/null" > queue_ai2_inspect.txt 2>&1
echo [4/4] ai2 inspect done %TIME% >> queue_master_log.txt

echo QUEUE DONE_ALL %DATE% %TIME% >> queue_master_log.txt
