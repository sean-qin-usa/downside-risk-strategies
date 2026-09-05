$ErrorActionPreference = 'Continue'
$PROJ  = 'C:\Users\OWNER\Claude\Projects\GBC Project'
$CLONE = 'C:\Users\OWNER\Claude\Projects\downside-risk-paper'
$log   = Join-Path $PROJ 'zz_jfec_sync19_log.txt'
"=== jfec_sync19 $(Get-Date -Format o) ===" | Out-File $log -Encoding utf8
Set-Location $PROJ
Copy-Item (Join-Path $PROJ 'frtb_table_canonical.py') (Join-Path $PROJ 'code\frtb_table.py') -Force
Copy-Item (Join-Path $PROJ 'job_causal_frontier.py')  (Join-Path $PROJ 'code\job_causal_frontier.py') -Force
Copy-Item (Join-Path $PROJ 'job_mechanism.py')        (Join-Path $PROJ 'code\job_mechanism.py') -Force
Copy-Item (Join-Path $PROJ 'job_fz_fullpanel.py')     (Join-Path $PROJ 'code\job_fz_fullpanel.py') -Force
if (-not (Test-Path (Join-Path $PROJ 'results'))) { New-Item -ItemType Directory -Path (Join-Path $PROJ 'results') | Out-Null }
foreach ($r in 'frtb_table_results.json','causal_frontier_results.json','fz_fullpanel_results.json','frtb_caviar_results.json','mechanism_results.json') {
  if (Test-Path (Join-Path $PROJ $r)) { Copy-Item (Join-Path $PROJ $r) (Join-Path $PROJ 'results') -Force }
}
git rm -r --cached --ignore-unmatch "*.csv" "*.csv.gz" "*.parquet" "*.pkl" "*.h5" 2>&1 | Out-Null
git add -A 2>&1 | Out-Null
git commit -m "R19 major-revision pass: mechanism experiment refutes model-relative claim (nu-relative has negative incremental content controlling for raw kurtosis) -- frontier is raw tail activity; CAViaR-extension MCS elimination fixed (HLN standardized range; MCS still {hybrid,CAViaR}); production ES recipe -> coherent Q*; Kupiec 81->84 pct; OA byline +Jiang; pre-registered wording; de-verdicted prose" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 3 | Out-File $log -Append -Encoding utf8
git log -1 --oneline 2>&1 | Out-File $log -Append -Encoding utf8
"--- push master ---" | Out-File $log -Append -Encoding utf8
git push origin master 2>&1 | Out-File $log -Append -Encoding utf8
"--- push main ---" | Out-File $log -Append -Encoding utf8
git push origin +master:main 2>&1 | Out-File $log -Append -Encoding utf8
git ls-remote origin master main 2>&1 | Out-File $log -Append -Encoding utf8
if (Test-Path $CLONE) {
  Set-Location $CLONE
  git pull 2>&1 | Out-Null
  if (-not (Test-Path 'submission')) { New-Item -ItemType Directory -Path 'submission' | Out-Null }
  foreach ($f in 'paper_A_jfec.pdf','paper_A_jfec.tex','paper_A_jfec_online_appendix.pdf','paper_A_jfec_online_appendix.tex') { Copy-Item (Join-Path $PROJ $f) 'submission\' -Force }
  foreach ($f in 'paper_A_frontier.pdf','paper_A_frontier.tex','refs_v3.bib','paper_A_online_appendix.tex') { Copy-Item (Join-Path $PROJ $f) '.' -Force }
  if (-not (Test-Path 'code')) { New-Item -ItemType Directory -Path 'code' | Out-Null }
  foreach ($c in 'frtb_table.py','frtb_caviar.py','job_causal_frontier.py','job_mechanism.py') { Copy-Item (Join-Path $PROJ 'code' $c) 'code\' -Force }
  if (-not (Test-Path 'results')) { New-Item -ItemType Directory -Path 'results' | Out-Null }
  foreach ($f in 'frtb_table_results.json','causal_frontier_results.json','fz_fullpanel_results.json','frtb_caviar_results.json','mechanism_results.json') { if (Test-Path (Join-Path $PROJ $f)) { Copy-Item (Join-Path $PROJ $f) 'results\' -Force } }
  git add -A 2>&1 | Out-Null
  git commit -m "R19 major-revision sync (paper + code + results)" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 3 | Out-File $log -Append -Encoding utf8
  "--- clone push ---" | Out-File $log -Append -Encoding utf8
  git push origin HEAD 2>&1 | Out-File $log -Append -Encoding utf8
} else { "CLONE not found, skipped" | Out-File $log -Append -Encoding utf8 }
"DONE" | Out-File $log -Append -Encoding utf8
