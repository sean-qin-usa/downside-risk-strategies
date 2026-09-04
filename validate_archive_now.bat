@echo off
REM Quick end-to-end validation (safe, fast): takes ONE intraday watchlist snapshot right now,
REM bypassing the market-hours guard (--force). Proves the host can pull yfinance chains and
REM write zstd parquet. Does NOT run the heavy full-universe sweep. Output -> validate_log.txt
cd /d "C:\Users\OWNER\Claude\Projects\GBC Project"
set "PYEXE=python"
if exist "%USERPROFILE%\anaconda3\python.exe" set "PYEXE=%USERPROFILE%\anaconda3\python.exe"
if exist "%USERPROFILE%\Anaconda3\python.exe" set "PYEXE=%USERPROFILE%\Anaconda3\python.exe"
if exist "C:\ProgramData\Anaconda3\python.exe" set "PYEXE=C:\ProgramData\Anaconda3\python.exe"
"%PYEXE%" -c "import yfinance" 2>nul || "%PYEXE%" -m pip install yfinance --quiet
"%PYEXE%" -c "import pyarrow"  2>nul || "%PYEXE%" -m pip install pyarrow  --quiet
set "CHAIN_ARCHIVE_ROOT=%USERPROFILE%\Box\GBC_data\chain_archive"
echo ==== VALIDATE %date% %time% ==== > "live_paper\validate_log.txt"
echo target=%CHAIN_ARCHIVE_ROOT% >> "live_paper\validate_log.txt"
"%PYEXE%" "live_paper\intraday_watchlist.py" --force >> "live_paper\validate_log.txt" 2>&1
echo ---- dir of today's intraday partition ---- >> "live_paper\validate_log.txt"
dir /s "%CHAIN_ARCHIVE_ROOT%\intraday" >> "live_paper\validate_log.txt" 2>&1
echo FIN_VALIDATE >> "live_paper\validate_log.txt"
