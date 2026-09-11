$ErrorActionPreference='Continue'
$PROJ='C:\Users\OWNER\Claude\Projects\GBC Project'
$CLONE='C:\Users\OWNER\Claude\Projects\downside-risk-paper'
$log=Join-Path $PROJ 'zz_sync_r19b_log.txt'
"=== r19b $(Get-Date -Format o) ===" | Out-File $log -Encoding utf8
Set-Location $PROJ
if (Test-Path '.git\index.lock') { Remove-Item '.git\index.lock' -Force }
git rm -r --cached --ignore-unmatch "*.csv" "*.csv.gz" "*.parquet" "*.pkl" "*.h5" 2>&1 | Out-Null
git add -A 2>&1 | Out-Null
git commit -m "R19b: tighten misspecification framing after the mechanism concession -- score is trailing kurtosis of standardized residuals (first-order departure from the fitted shape); only the finer per-name nu-normalization is rejected; title thesis defended precisely" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 3 | Out-File $log -Append -Encoding utf8
git log -1 --oneline 2>&1 | Out-File $log -Append -Encoding utf8
git push origin master 2>&1 | Out-File $log -Append -Encoding utf8
git push origin +master:main 2>&1 | Out-File $log -Append -Encoding utf8
git ls-remote origin master main 2>&1 | Out-File $log -Append -Encoding utf8
if (Test-Path $CLONE) {
  Set-Location $CLONE
  if (Test-Path '.git\index.lock') { Remove-Item '.git\index.lock' -Force }
  git pull 2>&1 | Out-Null
  if (-not (Test-Path 'submission')) { New-Item -ItemType Directory -Path 'submission' | Out-Null }
  foreach ($f in 'paper_A_jfec.pdf','paper_A_jfec.tex') { Copy-Item (Join-Path $PROJ $f) 'submission\' -Force }
  foreach ($f in 'paper_A_frontier.pdf','paper_A_frontier.tex') { Copy-Item (Join-Path $PROJ $f) '.' -Force }
  git add -A 2>&1 | Out-Null
  git commit -m "R19b framing sync" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" 2>&1 | Select-Object -First 3 | Out-File $log -Append -Encoding utf8
  git push origin HEAD 2>&1 | Out-File $log -Append -Encoding utf8
}
"DONE" | Out-File $log -Append -Encoding utf8
