$ErrorActionPreference = 'Continue'
$PROJ = 'C:\Users\OWNER\Claude\Projects\GBC Project'
$CLONE = 'C:\Users\OWNER\Claude\Projects\downside-risk-paper'
$log = Join-Path $PROJ 'zz_jfec_sync_log.txt'
"=== jfec_sync8 $(Get-Date -Format o) ===" | Out-File $log -Encoding utf8
Set-Location $PROJ
Copy-Item (Join-Path $PROJ 'frtb_bench_corrected.py') (Join-Path $PROJ 'code\frtb_bench.py') -Force
Copy-Item (Join-Path $PROJ 'job_wrds_holdout_patched.py') (Join-Path $PROJ 'code\job_wrds_holdout.py') -Force
Copy-Item (Join-Path $PROJ 'frtb_table_canonical.py') (Join-Path $PROJ 'code\frtb_table.py') -Force
Copy-Item (Join-Path $PROJ 'frtb_stress_exact.py') (Join-Path $PROJ 'code\frtb_stress_exact.py') -Force
git add -A 2>&1 | Out-Null
git commit -m "Wave-5: annual walk-forward confirms frontier (top decile +2.47 DM 6.05); conformal redefined as optional overlay; canonical ES artifacts; stale three-node scripts retired" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
git push origin master 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
git push origin +master:main 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
Set-Location $CLONE
git pull 2>&1 | Out-Null
if (-not (Test-Path 'submission')) { New-Item -ItemType Directory -Path 'submission' | Out-Null }
foreach ($f in 'paper_A_jfec.pdf','paper_A_jfec.tex','paper_A_jfec_online_appendix.pdf','paper_A_jfec_online_appendix.tex') {
  Copy-Item (Join-Path $PROJ $f) 'submission\' -Force
}
foreach ($f in 'paper_A_frontier.pdf','paper_A_frontier.tex','refs_v3.bib','README.md','paper_A_online_appendix.tex') {
  Copy-Item (Join-Path $PROJ $f) '.' -Force
}
Copy-Item (Join-Path $PROJ 'submission_README.md') 'submission\README.md' -Force
if (-not (Test-Path 'code')) { New-Item -ItemType Directory -Path 'code' | Out-Null }
Copy-Item (Join-Path $PROJ 'frtb_bench_corrected.py') 'code\frtb_bench.py' -Force
Copy-Item (Join-Path $PROJ 'code\job_wrds_holdout.py') 'code\' -Force
Copy-Item (Join-Path $PROJ 'code\frtb_table.py') 'code\' -Force
Copy-Item (Join-Path $PROJ 'code\frtb_stress_exact.py') 'code\' -Force
foreach ($stale in 'code\frtb_stress.py','results\frtb_stress_results.json','results\frtb_bench_results.json','frtb_stress_results.json','frtb_bench_results.json') {
  if (Test-Path $stale) { Remove-Item $stale -Force }
}
if (-not (Test-Path 'results')) { New-Item -ItemType Directory -Path 'results' | Out-Null }
foreach ($f in 'frtb_bench_v2_results.json','fz_aci_results.json','fhs_pername_results.json','holdout_recthr_results.json','romanowolf_results.json','calendar_split_results.json','calsplit2007_results.json','holdout_frozen_results.json','pit_universe_results.json','frtb_table_results.json','gas_polish_results.json','stress_es_results.json','walkforward_results.json') {
  if (Test-Path (Join-Path $PROJ $f)) { Copy-Item (Join-Path $PROJ $f) 'results\' -Force }
}
if (Test-Path 'frtb_bench_v2_results.json') { Copy-Item (Join-Path $PROJ 'frtb_bench_v2_results.json') '.' -Force }
if (Test-Path 'TUNING_GRID_PREREG.md') { Remove-Item 'TUNING_GRID_PREREG.md' -Force }
git add -A 2>&1 | Out-Null
git commit -m "Walk-forward confirmation; canonical script-to-JSON pairs; stale ES artifacts retired to history" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
git push origin HEAD 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
"DONE" | Out-File $log -Append -Encoding utf8
