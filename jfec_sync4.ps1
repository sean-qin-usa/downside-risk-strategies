$ErrorActionPreference = 'Continue'
$PROJ = 'C:\Users\OWNER\Claude\Projects\GBC Project'
$CLONE = 'C:\Users\OWNER\Claude\Projects\downside-risk-paper'
$log = Join-Path $PROJ 'zz_jfec_sync_log.txt'
"=== jfec_sync4 $(Get-Date -Format o) ===" | Out-File $log -Encoding utf8
Set-Location $PROJ
Copy-Item (Join-Path $PROJ 'frtb_bench_corrected.py') (Join-Path $PROJ 'code\frtb_bench.py') -Force
git add -A 2>&1 | Out-Null
git commit -m "Reviews 3-4 pass: corrected skew-t now canonical in code/, registered language retreat, CAViaR capabilities defense, overclaim narrowing, amortization leads contributions; ACI + per-name FHS + recursive-threshold jobs" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
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
Copy-Item (Join-Path $PROJ 'frtb_bench_v2_results.json') 'results\' -Force
if (Test-Path 'frtb_bench_v2_results.json') { Copy-Item (Join-Path $PROJ 'frtb_bench_v2_results.json') '.' -Force }
if (Test-Path 'TUNING_GRID_PREREG.md') { Remove-Item 'TUNING_GRID_PREREG.md' -Force }
git add -A 2>&1 | Out-Null
git commit -m "Corrected skew-t battery canonical (code + v2 results); frozen-specification language; per-name FHS and adaptive-conformal jobs announced; TUNING_GRID_PREREG (unrelated study) removed" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
git push origin HEAD 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
"DONE" | Out-File $log -Append -Encoding utf8
