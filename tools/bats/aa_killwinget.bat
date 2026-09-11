@echo off
echo === kill2 %date% %time% === > "%~dp0aa_killwinget_out.txt"
echo --- msiexec before --- >> "%~dp0aa_killwinget_out.txt"
tasklist /FI "IMAGENAME eq msiexec.exe" >> "%~dp0aa_killwinget_out.txt" 2>&1
taskkill /F /T /IM msiexec.exe >> "%~dp0aa_killwinget_out.txt" 2>&1
echo --- cmd list --- >> "%~dp0aa_killwinget_out.txt"
tasklist /FI "IMAGENAME eq cmd.exe" >> "%~dp0aa_killwinget_out.txt" 2>&1
echo --- winget again --- >> "%~dp0aa_killwinget_out.txt"
taskkill /F /T /IM winget.exe >> "%~dp0aa_killwinget_out.txt" 2>&1
echo DONE2 >> "%~dp0aa_killwinget_out.txt"
