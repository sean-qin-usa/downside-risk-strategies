@echo off
cd /d "C:\Users\OWNER\Claude\Projects\GBC Project"
set "PYEXE=python"
if exist "%USERPROFILE%\anaconda3\python.exe" set "PYEXE=%USERPROFILE%\anaconda3\python.exe"
if exist "%USERPROFILE%\Anaconda3\python.exe" set "PYEXE=%USERPROFILE%\Anaconda3\python.exe"
if exist "C:\ProgramData\Anaconda3\python.exe" set "PYEXE=C:\ProgramData\Anaconda3\python.exe"
"%PYEXE%" -c "import yfinance" 2>nul || "%PYEXE%" -m pip install yfinance --quiet
echo ==== %date% %time% ==== >> "live_paper\live_paper_log.txt"
"%PYEXE%" "live_paper\live_signal.py" >> "live_paper\live_paper_log.txt" 2>&1
"%PYEXE%" "live_paper\settle_tickets.py" >> "live_paper\live_paper_log.txt" 2>&1
echo FIN_LIVE_PAPER >> "live_paper\live_paper_log.txt"
