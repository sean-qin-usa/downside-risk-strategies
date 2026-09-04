@echo off
setlocal
set PROJ=C:\Users\OWNER\Claude\Projects\GBC Project
set LOG=%PROJ%\zz_reorg_log.txt
cd /d "%PROJ%"
echo === lock sweep === > "%LOG%"
powershell -NoProfile -Command "Get-ChildItem -Path '.git' -Recurse -Filter '*.lock' -File -ErrorAction SilentlyContinue | Where-Object {$_.LastWriteTime -lt (Get-Date).AddMinutes(-10)} | ForEach-Object { Remove-Item $_.FullName -Force }" >> "%LOG%" 2>&1
echo === pre-reorg snapshot commit === >> "%LOG%"
git add -A > nul 2>> "%LOG%"
git commit -m "pre-reorg snapshot" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" >> "%LOG%" 2>&1
echo === reorganize with git mv === >> "%LOG%"
powershell -NoProfile -Command ^
"$keep=@('paper_A_frontier.tex','paper_A_frontier.pdf','refs_v3.bib','README.md','RESEARCH_IDEAS_BACKLOG.md','START_RUNNER_CLICK_ME.bat','auto_runner.bat','.gitignore','.gitattributes');" ^
"foreach($d in 'paper','paper/archive_pdfs','code','results','logs','docs','figures','tools'){ if(-not (Test-Path $d)){ New-Item -ItemType Directory -Path $d | Out-Null } };" ^
"$files = git ls-files | Where-Object { $_ -notmatch '/' -and $keep -notcontains $_ };" ^
"foreach($f in $files){" ^
"  $dest=$null;" ^
"  if($f -match '\.py$'){ $dest='code' }" ^
"  elseif($f -match '\.json$'){ $dest='results' }" ^
"  elseif($f -match '\.png$'){ $dest='figures' }" ^
"  elseif($f -match '\.(txt|log)$'){ $dest='logs' }" ^
"  elseif($f -match '^(PaperA_|PaperB_|GRAFTQ_main|graftq).*\.pdf$'){ $dest='paper/archive_pdfs' }" ^
"  elseif($f -match '\.pdf$'){ $dest='docs' }" ^
"  elseif($f -match '\.tex$'){ $dest='paper' }" ^
"  elseif($f -match '\.(md|html)$'){ $dest='docs' }" ^
"  elseif($f -match '\.bat$'){ $dest='tools' }" ^
"  if($dest){ git mv -- \"$f\" \"$dest/$f\" 2>&1 | Out-Null; Write-Output \"$f -> $dest/\" } else { Write-Output \"$f (left in place)\" }" ^
"}" >> "%LOG%" 2>&1
echo === commit + push === >> "%LOG%"
git add -A > nul 2>> "%LOG%"
git commit -m "Reorganize repository into folders; README links the live draft" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" >> "%LOG%" 2>&1
git log -1 --oneline >> "%LOG%" 2>&1
git push origin master >> "%LOG%" 2>&1
git push origin +master:main >> "%LOG%" 2>&1
git status --porcelain | find /c /v "" >> "%LOG%" 2>&1
echo DONE >> "%LOG%"
