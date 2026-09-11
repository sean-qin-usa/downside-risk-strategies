$ErrorActionPreference = 'Continue'
$PROJ = 'C:\Users\OWNER\Claude\Projects\GBC Project'
$CLONE = 'C:\Users\OWNER\Claude\Projects\downside-risk-paper'
$log = Join-Path $PROJ 'zz_title_sync_log.txt'
"=== title_sync $(Get-Date -Format o) ===" | Out-File $log -Encoding utf8
Set-Location $PROJ
git add -A 2>&1 | Out-Null
git commit -m "Retitle: Semiparametric VaR and ES with a Real-Time Misspecification Score (JFEC register); resume one-entry form" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
git push origin master 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
git push origin +master:main 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
Set-Location $CLONE
git pull 2>&1 | Out-Null
Copy-Item (Join-Path $PROJ 'README_paper_repo.md') (Join-Path $CLONE 'README.md') -Force
Copy-Item (Join-Path $PROJ 'paper_A_frontier.pdf') $CLONE -Force
Copy-Item (Join-Path $PROJ 'paper_A_frontier.tex') $CLONE -Force
Copy-Item (Join-Path $PROJ 'docs\RESUME_BULLETS_2026-09.md') (Join-Path $CLONE 'docs\') -Force -ErrorAction SilentlyContinue
git add -A 2>&1 | Out-Null
git commit -m "Retitle to JFEC-register title; sync draft and README" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
git push origin HEAD 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
git log -1 --oneline 2>&1 | Out-File $log -Append -Encoding utf8
"DONE" | Out-File $log -Append -Encoding utf8
