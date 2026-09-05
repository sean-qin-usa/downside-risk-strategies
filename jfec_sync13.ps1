$ErrorActionPreference = 'Continue'
$PROJ = 'C:\Users\OWNER\Claude\Projects\GBC Project'
$CLONE = 'C:\Users\OWNER\Claude\Projects\downside-risk-paper'
$log = Join-Path $PROJ 'zz_jfec_sync_log.txt'
"=== jfec_sync13 $(Get-Date -Format o) ===" | Out-File $log -Encoding utf8
Set-Location $PROJ
Copy-Item (Join-Path $PROJ 'frtb_bench_corrected.py') (Join-Path $PROJ 'code\frtb_bench.py') -Force
Copy-Item (Join-Path $PROJ 'job_wrds_holdout_patched.py') (Join-Path $PROJ 'code\job_wrds_holdout.py') -Force
Copy-Item (Join-Path $PROJ 'frtb_table_canonical.py') (Join-Path $PROJ 'code\frtb_table.py') -Force
Copy-Item (Join-Path $PROJ 'job_stress_purged.py') (Join-Path $PROJ 'code\frtb_stress_exact.py') -Force
Copy-Item (Join-Path $PROJ 'job_horizon_purged.py') (Join-Path $PROJ 'code\job_horizon_purged.py') -Force
Copy-Item (Join-Path $PROJ 'job_fz_strict_calibration.py') (Join-Path $PROJ 'code\job_fz_strict_calibration.py') -Force
if (Test-Path (Join-Path $PROJ 'code\job_conformal_strict.py')) { Remove-Item (Join-Path $PROJ 'code\job_conformal_strict.py') -Force }
Copy-Item (Join-Path $PROJ 'job_stress_dm.py') (Join-Path $PROJ 'code\job_stress_dm.py') -Force
Copy-Item (Join-Path $PROJ 'job_nurel.py') (Join-Path $PROJ 'code\job_nurel.py') -Force
Copy-Item (Join-Path $PROJ 'job_coherent.py') (Join-Path $PROJ 'code\job_coherent.py') -Force
Copy-Item (Join-Path $PROJ 'job_fz_aci.py') (Join-Path $PROJ 'code\job_fz_aci.py') -Force
Copy-Item (Join-Path $PROJ 'job_fz_fullpanel.py') (Join-Path $PROJ 'code\job_fz_fullpanel.py') -Force
Copy-Item (Join-Path $PROJ 'fz_fullpanel_results.json') (Join-Path $PROJ 'results\fz_fullpanel_results.json') -Force
Copy-Item (Join-Path $PROJ 'job_fz_fullpanel.py') (Join-Path $PROJ 'code\job_fz_fullpanel.py') -Force
Copy-Item (Join-Path $PROJ 'fz_fullpanel_results.json') (Join-Path $PROJ 'results\fz_fullpanel_results.json') -Force
git add -A 2>&1 | Out-Null
git commit -m "Wave-9: nu-relative score test passes (top decile +3.0 DM 8.5); hybrid rewritten as coherent min-envelope curve (body binds 38pc, coherent ES marginally better); exact conformal order statistic; ACI under strict split; W1/DM-sign/lemma/EVT fixes; status-column and narration removed" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
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
Copy-Item (Join-Path $PROJ 'code\job_fz_strict_calibration.py') 'code\' -Force
foreach ($old in 'code\job_conformal_strict.py','results\fz_strict_results.json') { if (Test-Path $old) { Remove-Item $old -Force } }
Copy-Item (Join-Path $PROJ 'code\job_stress_dm.py') 'code\' -Force
Copy-Item (Join-Path $PROJ 'code\job_nurel.py') 'code\' -Force
Copy-Item (Join-Path $PROJ 'code\job_coherent.py') 'code\' -Force
Copy-Item (Join-Path $PROJ 'code\job_fz_aci.py') 'code\' -Force
Copy-Item (Join-Path $PROJ 'code\job_fz_fullpanel.py') 'code\' -Force
Copy-Item (Join-Path $PROJ 'results\fz_fullpanel_results.json') 'results\' -Force
Copy-Item (Join-Path $PROJ 'results\fz_fullpanel_results.json') 'results\' -Force
Copy-Item (Join-Path $PROJ 'job_fz_fullpanel.py') 'code\' -Force
foreach ($stale in 'code\frtb_stress.py','results\frtb_stress_results.json','results\frtb_bench_results.json','frtb_stress_results.json','frtb_bench_results.json') {
  if (Test-Path $stale) { Remove-Item $stale -Force }
}
if (-not (Test-Path 'results')) { New-Item -ItemType Directory -Path 'results' | Out-Null }
foreach ($f in 'frtb_bench_v2_results.json','fz_aci_results.json','fhs_pername_results.json','holdout_recthr_results.json','romanowolf_results.json','calendar_split_results.json','calsplit2007_results.json','holdout_frozen_results.json','pit_universe_results.json','frtb_table_results.json','gas_polish_results.json','stress_es_results.json','walkforward_results.json','horizon_purged_results.json','fz_strict_calibration_results.json','nurel_results.json','coherent_results.json','fz_aci_results.json') {
  if (Test-Path (Join-Path $PROJ $f)) { Copy-Item (Join-Path $PROJ $f) 'results\' -Force }
}
foreach ($py in 'gpu_iqn_amort.py','gpu_iqn_frozen.py','pulled_gpu_iqn_mh.py') {
  if (Test-Path $py) { Move-Item $py 'code\' -Force }
}
Get-ChildItem -Path . -Filter *.json -File | ForEach-Object { Move-Item $_.FullName 'results\' -Force }
git add -A 2>&1 | Out-Null
git commit -m "Coherent hybrid equation and audit artifacts; nu-relative score test; exact-order-statistic conformal reruns; declarative abstract; scoreboard language removed" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
git push origin HEAD 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
"DONE" | Out-File $log -Append -Encoding utf8
