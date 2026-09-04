@echo off
REM ===========================================================================
REM  run_chain_archive.bat  — daily FULL option-chain archive (all optionable US)
REM  Heavy/long-running. Writes zstd parquet to C:\GBC_data\chain_archive, then
REM  mirrors to Google Drive. Independent of the live trading signal.
REM ===========================================================================
cd /d "C:\Users\OWNER\Claude\Projects\GBC Project"

set "PYEXE=python"
if exist "%USERPROFILE%\anaconda3\python.exe" set "PYEXE=%USERPROFILE%\anaconda3\python.exe"
if exist "%USERPROFILE%\Anaconda3\python.exe" set "PYEXE=%USERPROFILE%\Anaconda3\python.exe"
if exist "C:\ProgramData\Anaconda3\python.exe" set "PYEXE=C:\ProgramData\Anaconda3\python.exe"

REM --- dependencies -----------------------------------------------------------
"%PYEXE%" -c "import yfinance" 2>nul || "%PYEXE%" -m pip install yfinance --quiet
"%PYEXE%" -c "import pyarrow"  2>nul || "%PYEXE%" -m pip install pyarrow  --quiet
"%PYEXE%" -c "import pandas"   2>nul || "%PYEXE%" -m pip install pandas   --quiet

REM --- storage: primary = Box mount (streams to Box cloud, keeps C: light) -----
set "CHAIN_ARCHIVE_ROOT=%USERPROFILE%\Box\GBC_data\chain_archive"

set "LOG=live_paper\chain_archive_log.txt"
echo ==== %date% %time% ==== >> "%LOG%"
echo target=%CHAIN_ARCHIVE_ROOT% >> "%LOG%"

REM --- refresh optionable universe (skips itself if cache < 7 days old) --------
"%PYEXE%" "live_paper\build_optionable_universe.py" >> "%LOG%" 2>&1

REM --- capture today's full chains --------------------------------------------
"%PYEXE%" "live_paper\chain_archive.py" >> "%LOG%" 2>&1

echo FIN_CHAIN_ARCHIVE >> "%LOG%"
