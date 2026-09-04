@echo off
setlocal
set PROJ=C:\Users\OWNER\Claude\Projects\GBC Project
set LOG=%PROJ%\gitpush4_log.txt
cd /d "%PROJ%"
echo === lock sweep === > "%LOG%"
powershell -NoProfile -Command "Get-ChildItem -Path '.git' -Recurse -Filter '*.lock' -File -ErrorAction SilentlyContinue | Where-Object {$_.LastWriteTime -lt (Get-Date).AddMinutes(-10)} | ForEach-Object { $_.FullName; Remove-Item $_.FullName -Force }" >> "%LOG%" 2>&1
git add -A > nul 2>> "%LOG%"
git commit -m "fig:holdout caption: separate pooled decile means (+1.01) from per-date DM statistic (+0.89, DM 2.16)" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" >> "%LOG%" 2>&1
git log -1 --oneline >> "%LOG%" 2>&1
git push origin master >> "%LOG%" 2>&1
git status --porcelain | find /c /v "" >> "%LOG%" 2>&1
echo DONE >> "%LOG%"
