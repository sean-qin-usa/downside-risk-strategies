@echo off
REM ===========================================================================
REM  run_intraday_watchlist.bat — ONE intraday snapshot of the watchlist chains.
REM  Fired every ~15 min during market hours by Task Scheduler. Fast (small N).
REM ===========================================================================
cd /d "C:\Users\OWNER\Claude\Projects\GBC Project"

set "PYEXE=python"
if exist "%USERPROFILE%\anaconda3\python.exe" set "PYEXE=%USERPROFILE%\anaconda3\python.exe"
if exist "%USERPROFILE%\Anaconda3\python.exe" set "PYEXE=%USERPROFILE%\Anaconda3\python.exe"
if exist "C:\ProgramData\Anaconda3\python.exe" set "PYEXE=C:\ProgramData\Anaconda3\python.exe"

"%PYEXE%" -c "import yfinance" 2>nul || "%PYEXE%" -m pip install yfinance --quiet
"%PYEXE%" -c "import pyarrow"  2>nul || "%PYEXE%" -m pip install pyarrow  --quiet

REM --- storage: primary = Box mount (streams to Box cloud) ---------------------
set "CHAIN_ARCHIVE_ROOT=%USERPROFILE%\Box\GBC_data\chain_archive"

set "LOG=live_paper\intraday_log.txt"
echo ==== %date% %time% ==== >> "%LOG%"
"%PYEXE%" "live_paper\intraday_watchlist.py" >> "%LOG%" 2>&1
echo FIN_INTRADAY >> "%LOG%"
