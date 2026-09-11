$ErrorActionPreference='Continue'
$PROJ='C:\Users\OWNER\Claude\Projects\GBC Project'
$CLONE='C:\Users\OWNER\Claude\Projects\downside-risk-paper'
$log=Join-Path $PROJ 'zz_jfec_sync_log.txt'
"=== jfec_sync27 (coauthor e-mail) $(Get-Date -Format o) ===" | Out-File $log -Encoding utf8
Set-Location $PROJ
if(Test-Path '.git\index.lock'){Remove-Item '.git\index.lock' -Force}
git add -A 2>&1 | Out-Null
git commit -m "Title block: add coauthor e-mail (Wenxin Jiang, wjiang@northwestern.edu); both authors now list e-mail, shared department affiliation" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
git push origin master 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
git push origin +master:main 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
Set-Location $CLONE
if(Test-Path '.git\index.lock'){Remove-Item '.git\index.lock' -Force}
git pull 2>&1 | Out-Null
foreach($f in 'paper_A_jfec.pdf','paper_A_jfec.tex'){Copy-Item (Join-Path $PROJ $f) 'submission\' -Force}
foreach($f in 'paper_A_frontier.pdf','paper_A_frontier.tex'){Copy-Item (Join-Path $PROJ $f) '.' -Force}
git add -A 2>&1 | Out-Null
git commit -m "Title block: add coauthor e-mail (Wenxin Jiang); both builds" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
git push origin HEAD 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
"DONE email" | Out-File $log -Append -Encoding utf8
