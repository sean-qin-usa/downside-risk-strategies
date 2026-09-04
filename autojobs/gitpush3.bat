@echo off
setlocal
set PROJ=C:\Users\OWNER\Claude\Projects\GBC Project
set LOG=%PROJ%\gitpush3_log.txt
cd /d "%PROJ%"
echo === kill ALL stale git locks over 10 min old === > "%LOG%"
powershell -NoProfile -Command "Get-ChildItem -Path '.git' -Recurse -Filter '*.lock' -File -ErrorAction SilentlyContinue | Where-Object {$_.LastWriteTime -lt (Get-Date).AddMinutes(-10)} | ForEach-Object { $_.FullName; Remove-Item $_.FullName -Force }" >> "%LOG%" 2>&1
echo === safety: untrack licensed data === >> "%LOG%"
git rm -r --cached --ignore-unmatch "*.csv" "*.csv.gz" "*.parquet" "*.pkl" "*.h5" "data" "panels" "holdout_panel_2000_2013.csv" >> "%LOG%" 2>&1
echo === add + commit === >> "%LOG%"
git add -A > nul 2>> "%LOG%"
git commit -m "Journal-readiness batch: 2000-2013 frozen-spec holdout + timing diagnostics + per-asset v2 restatement + wins-led paper restructure" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" >> "%LOG%" 2>&1
echo === last commit === >> "%LOG%"
git log -1 --oneline >> "%LOG%" 2>&1
git diff --shortstat HEAD~1..HEAD >> "%LOG%" 2>&1
echo === push === >> "%LOG%"
git push origin master >> "%LOG%" 2>&1
echo === remaining uncommitted count === >> "%LOG%"
git status --porcelain | find /c /v "" >> "%LOG%" 2>&1
echo DONE >> "%LOG%"
