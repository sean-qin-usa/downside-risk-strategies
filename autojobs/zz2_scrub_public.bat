@echo off
setlocal
set PROJ=C:\Users\OWNER\Claude\Projects\GBC Project
set LOG=%PROJ%\zz2_scrub_log.txt
cd /d "%PROJ%"
echo === 0 preflight: clean stale locks === > "%LOG%"
powershell -NoProfile -Command "Get-ChildItem -Path '.git' -Recurse -Filter '*.lock' -File -ErrorAction SilentlyContinue | Where-Object {$_.LastWriteTime -lt (Get-Date).AddMinutes(-10)} | ForEach-Object { $_.FullName; Remove-Item $_.FullName -Force }" >> "%LOG%" 2>&1
echo === 1 ensure fully committed before rewrite === >> "%LOG%"
git add -A > nul 2>> "%LOG%"
git commit -m "pre-scrub sync" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" >> "%LOG%" 2>&1
git status --porcelain | find /c /v "" >> "%LOG%" 2>&1
echo === 2 local backups of paths being scrubbed === >> "%LOG%"
if not exist "_scrub_backup" mkdir "_scrub_backup"
if exist "_github_private" robocopy "_github_private" "_scrub_backup\_github_private" /E /NFL /NDL /NJH /NJS >> "%LOG%" 2>&1
if exist "tpx_inspect_out.txt" copy /y "tpx_inspect_out.txt" "_scrub_backup\tpx_inspect_out.txt" >> "%LOG%" 2>&1
echo _scrub_backup/ >> .gitignore
echo _github_private/ >> .gitignore
echo tpx_inspect_out.txt >> .gitignore
git add .gitignore >> "%LOG%" 2>&1
git commit -m "gitignore: exclude private folder and scrubbed inspect file" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" >> "%LOG%" 2>&1
echo === 3 install git-filter-repo === >> "%LOG%"
python -m pip install --quiet --disable-pip-version-check git-filter-repo >> "%LOG%" 2>&1
echo === 4 scrub history: tpx_inspect_out.txt + _github_private === >> "%LOG%"
python -m git_filter_repo --invert-paths --path tpx_inspect_out.txt --path _github_private --force >> "%LOG%" 2>&1
echo filterrepo_exit=%ERRORLEVEL% >> "%LOG%"
echo === 5 restore remote + force push === >> "%LOG%"
git remote add origin https://github.com/sean-qin-usa/downside-risk-strategies.git >> "%LOG%" 2>&1
git push origin --force --all >> "%LOG%" 2>&1
git push origin --force --tags >> "%LOG%" 2>&1
echo === 6 restore local copies, now untracked and ignored === >> "%LOG%"
if exist "_scrub_backup\_github_private" robocopy "_scrub_backup\_github_private" "_github_private" /E /NFL /NDL /NJH /NJS >> "%LOG%" 2>&1
if exist "_scrub_backup\tpx_inspect_out.txt" copy /y "_scrub_backup\tpx_inspect_out.txt" "tpx_inspect_out.txt" >> "%LOG%" 2>&1
echo === 7 refined audit: extension-anchored data files + scrub check === >> "%LOG%"
git log --all --pretty=format: --name-only | findstr /R /I /C:"\.csv$" /C:"\.gz$" /C:"\.parquet$" /C:"\.pkl$" /C:"\.h5$" /C:"\.zip$" /C:"\.sas7bdat$" /C:"\.dta$" /C:"\.feather$" > "%PROJ%\_audit_hits.txt" 2>&1
git log --all --pretty=format: --name-only | findstr /I /C:"tpx_inspect_out" /C:"_github_private" >> "%PROJ%\_audit_hits.txt" 2>&1
for %%A in ("%PROJ%\_audit_hits.txt") do set HITSIZE=%%~zA
echo audit_hits_bytes=%HITSIZE% >> "%LOG%"
type "%PROJ%\_audit_hits.txt" >> "%LOG%"
if "%HITSIZE%"=="0" (
  echo VERDICT: CLEAN -- flipping repo PUBLIC >> "%LOG%"
  gh repo edit sean-qin-usa/downside-risk-strategies --visibility public --accept-visibility-change-consequences >> "%LOG%" 2>&1
  gh repo view sean-qin-usa/downside-risk-strategies --json visibility >> "%LOG%" 2>&1
) else (
  echo VERDICT: hits remain -- NOT flipping public >> "%LOG%"
)
echo DONE >> "%LOG%"
