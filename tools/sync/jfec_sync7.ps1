$ErrorActionPreference = 'Continue'
$PROJ = 'C:\Users\OWNER\Claude\Projects\GBC Project'
$CLONE = 'C:\Users\OWNER\Claude\Projects\downside-risk-paper'
$log = Join-Path $PROJ 'zz_jfec_sync_log.txt'
"=== jfec_sync7 $(Get-Date -Format o) ===" | Out-File $log -Encoding utf8
Set-Location $PROJ
Copy-Item (Join-Path $PROJ 'frtb_bench_corrected.py') (Join-Path $PROJ 'code\frtb_bench.py') -Force
Copy-Item (Join-Path $PROJ 'job_wrds_holdout_patched.py') (Join-Path $PROJ 'code\job_wrds_holdout.py') -Force
git add -A 2>&1 | Out-Null
git commit -m "Wave-4 pass: true ten-day ES both eras, FRTB-aligned framing, gradient thesis, production-box cold-start fix, repo registered-sweep, kurtosis-attenuation defense" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
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
if (-not (Test-Path 'results')) { New-Item -ItemType Directory -Path 'results' | Out-Null }
foreach ($f in 'frtb_bench_v2_results.json','fz_aci_results.json','fhs_pername_results.json','holdout_recthr_results.json','romanowolf_results.json','calendar_split_results.json','calsplit2007_results.json','holdout_frozen_results.json','pit_universe_results.json','frtb_table_results.json','gas_polish_results.json','stress_es_results.json') {
  if (Test-Path (Join-Path $PROJ $f)) { Copy-Item (Join-Path $PROJ $f) 'results\' -Force }
}
if (Test-Path 'frtb_bench_v2_results.json') { Copy-Item (Join-Path $PROJ 'frtb_bench_v2_results.json') '.' -Force }
if (Test-Path 'TUNING_GRID_PREREG.md') { Remove-Item 'TUNING_GRID_PREREG.md' -Force }
git add -A 2>&1 | Out-Null
git commit -m "Ten-day true ES; FRTB-aligned framing; gradient thesis; registered sweep complete" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
git push origin HEAD 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
"DONE" | Out-File $log -Append -Encoding utf8
