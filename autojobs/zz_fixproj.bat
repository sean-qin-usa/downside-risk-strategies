@echo off
setlocal
set PROJ=C:\Users\OWNER\Claude\Projects\GBC Project
set LOG=%PROJ%\zz_fixproj_log.txt
cd /d "%PROJ%"
echo === fixproj %date% %time% === > "%LOG%"
if exist ".git\index.lock" del /f /q ".git\index.lock" >> "%LOG%" 2>&1
echo lock cleared >> "%LOG%"
git rm -r --cached --ignore-unmatch "*.csv" "*.csv.gz" "*.parquet" "*.pkl" "*.h5" >> "%LOG%" 2>&1
git add -A >> "%LOG%" 2>&1
git commit -m "R19 major-revision pass: mechanism experiment refutes model-relative claim (nu-relative negative incremental content vs raw kurtosis); CAViaR MCS elimination fixed (HLN range; MCS still {hybrid,CAViaR}, DM 0.4); production ES -> coherent Q*; Kupiec 81->84; OA byline +Jiang; pre-registered wording; de-verdicted prose" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" >> "%LOG%" 2>&1
git log -1 --oneline >> "%LOG%" 2>&1
git push origin master >> "%LOG%" 2>&1
git push origin +master:main >> "%LOG%" 2>&1
git ls-remote origin master main >> "%LOG%" 2>&1
echo DONE >> "%LOG%"
