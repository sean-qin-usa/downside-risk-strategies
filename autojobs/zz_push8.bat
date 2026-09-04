@echo off
setlocal
set PROJ=C:\Users\OWNER\Claude\Projects\GBC Project
set LOG=%PROJ%\zz_push8_log.txt
cd /d "%PROJ%"
echo === lock sweep === > "%LOG%"
powershell -NoProfile -Command "Get-ChildItem -Path '.git' -Recurse -Filter '*.lock' -File -ErrorAction SilentlyContinue | Where-Object {$_.LastWriteTime -lt (Get-Date).AddMinutes(-10)} | ForEach-Object { $_.FullName; Remove-Item $_.FullName -Force }" >> "%LOG%" 2>&1
echo === remote refs before === >> "%LOG%"
git ls-remote origin >> "%LOG%" 2>&1
echo === safety: untrack licensed data === >> "%LOG%"
git rm -r --cached --ignore-unmatch "*.csv" "*.csv.gz" "*.parquet" "*.pkl" "*.h5" "holdout_panel_2000_2013.csv" >> "%LOG%" 2>&1
git add -A > nul 2>> "%LOG%"
git commit -m "Paper v09-04c: stress-era + FZ0 results folded; ledger + float-layout fixes; 34pp" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" >> "%LOG%" 2>&1
git log -1 --oneline >> "%LOG%" 2>&1
echo === push master and sync main === >> "%LOG%"
git push origin master >> "%LOG%" 2>&1
git push origin +master:main >> "%LOG%" 2>&1
echo === remote refs after === >> "%LOG%"
git ls-remote origin >> "%LOG%" 2>&1
git status --porcelain | find /c /v "" >> "%LOG%" 2>&1
echo DONE >> "%LOG%"
