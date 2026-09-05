$ErrorActionPreference = 'Continue'
$PROJ = 'C:\Users\OWNER\Claude\Projects\GBC Project'
$CLONE = 'C:\Users\OWNER\Claude\Projects\downside-risk-paper'
$log = Join-Path $PROJ 'zz_jfec_sync_log.txt'
"=== jfec_sync24 (R20) $(Get-Date -Format o) ===" | Out-File $log -Encoding utf8
Set-Location $PROJ
if (Test-Path '.git\index.lock') { Remove-Item '.git\index.lock' -Force }
# --- mirror R20 code + results into the tracked code/ and results/ (public replication surface) ---
Copy-Item (Join-Path $PROJ 'job_wrds_holdout_patched.py') (Join-Path $PROJ 'code\job_wrds_holdout.py') -Force
Copy-Item (Join-Path $PROJ 'job_composite.py')          (Join-Path $PROJ 'code\job_composite.py') -Force
if (Test-Path (Join-Path $PROJ 'composite_results.json')) { Copy-Item (Join-Path $PROJ 'composite_results.json') (Join-Path $PROJ 'results\composite_results.json') -Force }
if (Test-Path (Join-Path $PROJ 'mechanism_results.json')) { Copy-Item (Join-Path $PROJ 'mechanism_results.json') (Join-Path $PROJ 'results\mechanism_results.json') -Force }
git add -A 2>&1 | Out-Null
git commit -m "R20: evaluate the deployed composite score (top decile +2.79%/DM 8.9; causal expanding cutoff +2.72%/DM 9.0); Algorithm 4/OA.2 step (iii) reworded from 'rank of the maximum' to the evaluated max-of-percentiles re-deciled score; scrub WRDS username + C:\\Users path from code/job_wrds_holdout.py (env vars); four text fixes (governs->predicts, conformal motivated-by not guaranteed, kurtosis-variance asymptotics corrected, day-level timing removed); conclusion+composite tightened to hold length" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
git push origin master 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
git push origin +master:main 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
# --- CLONE (downside-risk-paper: submission + curated public replication) ---
Set-Location $CLONE
if (Test-Path '.git\index.lock') { Remove-Item '.git\index.lock' -Force }
git pull 2>&1 | Out-Null
if (-not (Test-Path 'submission')) { New-Item -ItemType Directory -Path 'submission' | Out-Null }
foreach ($f in 'paper_A_jfec.pdf','paper_A_jfec.tex','paper_A_jfec_online_appendix.pdf','paper_A_jfec_online_appendix.tex') { Copy-Item (Join-Path $PROJ $f) 'submission\' -Force }
foreach ($f in 'paper_A_frontier.pdf','paper_A_frontier.tex','refs_v3.bib') { Copy-Item (Join-Path $PROJ $f) '.' -Force }
if (-not (Test-Path 'code')) { New-Item -ItemType Directory -Path 'code' | Out-Null }
Copy-Item (Join-Path $PROJ 'code\job_wrds_holdout.py') 'code\' -Force
Copy-Item (Join-Path $PROJ 'code\job_composite.py')    'code\' -Force
if (-not (Test-Path 'results')) { New-Item -ItemType Directory -Path 'results' | Out-Null }
if (Test-Path (Join-Path $PROJ 'results\composite_results.json')) { Copy-Item (Join-Path $PROJ 'results\composite_results.json') 'results\' -Force }
git add -A 2>&1 | Out-Null
git commit -m "R20: deployed-composite evaluation folded in (+2.79%/DM 8.9, causal +2.72%/DM 9.0); Algorithm OA.2 (iii) reworded to the evaluated score; job_wrds_holdout.py credential/path leak scrubbed to env vars; job_composite.py + composite_results.json added; four text fixes; submission text held under the 40-page double-spaced limit" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
git push origin HEAD 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
"DONE R20" | Out-File $log -Append -Encoding utf8
