@echo off
set G=C:\Users\OWNER\Claude\Projects\GBC Project
echo WEEKLY_SIGNAL_START %date% %time% > "%G%\weekly_signal_done.txt"
cd /d %USERPROFILE%
call anaconda3\Scripts\activate.bat
python "%G%\weekly_signal_gen.py" >> "%G%\weekly_signal_done.txt" 2>&1
echo WEEKLY_SIGNAL_EXIT_RC=%errorlevel% >> "%G%\weekly_signal_done.txt"
echo WEEKLY_SIGNAL_DONE %date% %time% >> "%G%\weekly_signal_done.txt"
