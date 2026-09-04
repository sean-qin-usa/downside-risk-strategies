$ErrorActionPreference = 'Continue'
$PROJ = 'C:\Users\OWNER\Claude\Projects\GBC Project'
$CLONE = 'C:\Users\OWNER\Claude\Projects\downside-risk-paper'
$log = Join-Path $PROJ 'zz_jfec_sync_log.txt'
"=== jfec_sync11 $(Get-Date -Format o) ===" | Out-File $log -Encoding utf8
Set-Location $PROJ
Copy-Item (Join-Path $PROJ 'frtb_bench_corrected.py') (Join-Path $PROJ 'code\frtb_bench.py') -Force
Copy-Item (Join-Path $PROJ 'job_wrds_holdout_patched.py') (Join-Path $PROJ 'code\job_wrds_holdout.py') -Force
Copy-Item (Join-Path $PROJ 'frtb_table_canonical.py') (Join-Path $PROJ 'code\frtb_table.py') -Force
Copy-Item (Join-Path $PROJ 'job_stress_purged.py') (Join-Path $PROJ 'code\frtb_stress_exact.py') -Force
Copy-Item (Join-Path $PROJ 'job_horizon_purged.py') (Join-Path $PROJ 'code\job_horizon_purged.py') -Force
Copy-Item (Join-Path $PROJ 'job_conformal_strict.py') (Join-Path $PROJ 'code\job_conformal_strict.py') -Force
Copy-Item (Join-Path $PROJ 'job_stress_dm.py') (Join-Path $PROJ 'code\job_stress_dm.py') -Force
Copy-Item (Join-Path $PROJ 'job_fz_fullpanel.py') (Join-Path $PROJ 'code\job_fz_fullpanel.py') -Force
git add -A 2>&1 | Out-Null
git commit -m "Wave-7: strict-split conformal audit with matched-information control (advantage intact, DM 5.0/5.3); out-of-era edge stored in-artifact (+0.49, DM 0.07); abstract per-name wording; ten-day row moved out of engine panel; conclusion tightened" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
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
Copy-Item (Join-Path $PROJ 'code\job_horizon_purged.py') 'code\' -Force
Copy-Item (Join-Path $PROJ 'code\job_conformal_strict.py') 'code\' -Force
Copy-Item (Join-Path $PROJ 'code\job_stress_dm.py') 'code\' -Force
Copy-Item (Join-Path $PROJ 'results\fz_fullpanel_results.json') 'results\' -Force
Copy-Item (Join-Path $PROJ 'job_fz_fullpanel.py') 'code\' -Force
foreach ($stale in 'code\frtb_stress.py','results\frtb_stress_results.json','results\frtb_bench_results.json','frtb_stress_results.json','frtb_bench_results.json') {
  if (Test-Path $stale) { Remove-Item $stale -Force }
}
if (-not (Test-Path 'results')) { New-Item -ItemType Directory -Path 'results' | Out-Null }
foreach ($f in 'frtb_bench_v2_results.json','fz_aci_results.json','fhs_pername_results.json','holdout_recthr_results.json','romanowolf_results.json','calendar_split_results.json','calsplit2007_results.json','holdout_frozen_results.json','pit_universe_results.json','frtb_table_results.json','gas_polish_results.json','stress_es_results.json','walkforward_results.json','horizon_purged_results.json','fz_strict_results.json') {
  if (Test-Path (Join-Path $PROJ $f)) { Copy-Item (Join-Path $PROJ $f) 'results\' -Force }
}
foreach ($py in 'gpu_iqn_amort.py','gpu_iqn_frozen.py','pulled_gpu_iqn_mh.py') {
  if (Test-Path $py) { Move-Item $py 'code\' -Force }
}
Get-ChildItem -Path . -Filter *.json -File | ForEach-Object { Move-Item $_.FullName 'results\' -Force }
git add -A 2>&1 | Out-Null
git commit -m "Strict-split audit artifacts; per-name calibration wording; extension block in summary table; provenance-aligned out-of-era numbers" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
git push origin HEAD 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
"DONE" | Out-File $log -Append -Encoding utf8
