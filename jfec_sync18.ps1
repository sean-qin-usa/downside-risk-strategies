$ErrorActionPreference = 'Continue'
$PROJ  = 'C:\Users\OWNER\Claude\Projects\GBC Project'
$CLONE = 'C:\Users\OWNER\Claude\Projects\downside-risk-paper'
$log   = Join-Path $PROJ 'zz_jfec_sync18_log.txt'
"=== jfec_sync18 $(Get-Date -Format o) ===" | Out-File $log -Encoding utf8
Set-Location $PROJ
# mirror canonical scripts -> code/
Copy-Item (Join-Path $PROJ 'frtb_table_canonical.py') (Join-Path $PROJ 'code\frtb_table.py') -Force
Copy-Item (Join-Path $PROJ 'job_causal_frontier.py')  (Join-Path $PROJ 'code\job_causal_frontier.py') -Force
Copy-Item (Join-Path $PROJ 'job_fz_fullpanel.py')     (Join-Path $PROJ 'code\job_fz_fullpanel.py') -Force
# mirror fresh results -> results/
if (-not (Test-Path (Join-Path $PROJ 'results'))) { New-Item -ItemType Directory -Path (Join-Path $PROJ 'results') | Out-Null }
foreach ($r in 'frtb_table_results.json','causal_frontier_results.json','fz_fullpanel_results.json') {
  if (Test-Path (Join-Path $PROJ $r)) { Copy-Item (Join-Path $PROJ $r) (Join-Path $PROJ 'results') -Force }
}
# safety: never commit licensed data
git rm -r --cached --ignore-unmatch "*.csv" "*.csv.gz" "*.parquet" "*.pkl" "*.h5" 2>&1 | Out-Null
git add -A 2>&1 | Out-Null
git commit -m "R18 hardening: causal decile-cutoff robustness (86 pct membership overlap, top +2.45 pct DM 8.3); MCS elimination -> HLN standardized range (sole survivor unchanged); OA table refs off-by-one fixed; Kupiec pass-rate figure regenerated from canonical skew-t set; GAS demoted to indicative-only; paper-wide multiplicity framing" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 3 | Out-File $log -Append -Encoding utf8
git log -1 --oneline 2>&1 | Out-File $log -Append -Encoding utf8
"--- push master ---" | Out-File $log -Append -Encoding utf8
git push origin master 2>&1 | Out-File $log -Append -Encoding utf8
"--- push main ---" | Out-File $log -Append -Encoding utf8
git push origin +master:main 2>&1 | Out-File $log -Append -Encoding utf8
"--- remote refs ---" | Out-File $log -Append -Encoding utf8
git ls-remote origin master main 2>&1 | Out-File $log -Append -Encoding utf8
# --- CLONE (public paper repo), guarded ---
if (Test-Path $CLONE) {
  Set-Location $CLONE
  git pull 2>&1 | Out-Null
  if (-not (Test-Path 'submission')) { New-Item -ItemType Directory -Path 'submission' | Out-Null }
  foreach ($f in 'paper_A_jfec.pdf','paper_A_jfec.tex','paper_A_jfec_online_appendix.pdf','paper_A_jfec_online_appendix.tex') { Copy-Item (Join-Path $PROJ $f) 'submission\' -Force }
  foreach ($f in 'paper_A_frontier.pdf','paper_A_frontier.tex','refs_v3.bib','paper_A_online_appendix.tex') { Copy-Item (Join-Path $PROJ $f) '.' -Force }
  if (-not (Test-Path 'code')) { New-Item -ItemType Directory -Path 'code' | Out-Null }
  Copy-Item (Join-Path $PROJ 'code\frtb_table.py') 'code\' -Force
  Copy-Item (Join-Path $PROJ 'code\job_causal_frontier.py') 'code\' -Force
  if (-not (Test-Path 'results')) { New-Item -ItemType Directory -Path 'results' | Out-Null }
  foreach ($f in 'frtb_table_results.json','causal_frontier_results.json','fz_fullpanel_results.json') { if (Test-Path (Join-Path $PROJ $f)) { Copy-Item (Join-Path $PROJ $f) 'results\' -Force } }
  git add -A 2>&1 | Out-Null
  git commit -m "R18 hardening sync (paper builds + code + results)" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 3 | Out-File $log -Append -Encoding utf8
  "--- clone push ---" | Out-File $log -Append -Encoding utf8
  git push origin HEAD 2>&1 | Out-File $log -Append -Encoding utf8
} else { "CLONE not found, skipped" | Out-File $log -Append -Encoding utf8 }
"DONE" | Out-File $log -Append -Encoding utf8
