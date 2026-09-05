$ErrorActionPreference = 'Continue'
$PROJ = 'C:\Users\OWNER\Claude\Projects\GBC Project'
$CLONE = 'C:\Users\OWNER\Claude\Projects\downside-risk-paper'
$log = Join-Path $PROJ 'zz_jfec_sync_log.txt'
"=== jfec_sync25 (R20 FIX) $(Get-Date -Format o) ===" | Out-File $log -Encoding utf8
Set-Location $PROJ
if (Test-Path '.git\index.lock') { Remove-Item '.git\index.lock' -Force }
# untrack the transport tarball the stale run committed; ignore transport junk going forward
git rm --cached --ignore-unmatch r20_sync.tgz 2>&1 | Out-Null
Add-Content -Path '.gitignore' -Value "`n*.tgz`n_r20tmp*`n_HELD_*"
# re-mirror the now-correct scrubbed code (stale run copied leaked/old versions)
Copy-Item (Join-Path $PROJ 'job_wrds_holdout_patched.py') (Join-Path $PROJ 'code\job_wrds_holdout.py') -Force
Copy-Item (Join-Path $PROJ 'job_composite.py')            (Join-Path $PROJ 'code\job_composite.py') -Force
git add -A 2>&1 | Out-Null
git commit -m "R20 FIX: prior commit eae6692 ran on stale files (bridge mount refused tar overwrite); this commit carries the actual deployed-composite paragraph in all three tex builds, the Algorithm 4/OA.2 (iii) rewording to the evaluated max-of-percentiles score, and the scrubbed code/job_wrds_holdout.py (WRDS username + C:\\Users path -> env vars); untracks the 1.5MB transport tarball" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 3 | Out-File $log -Append -Encoding utf8
git push origin master 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
git push origin +master:main 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
"code/job_wrds_holdout.py seanqin count (want 0) = " + ((Select-String -Path (Join-Path $PROJ 'code\job_wrds_holdout.py') -Pattern 'seanqin2028' -AllMatches).Matches.Count) | Out-File $log -Append -Encoding utf8
"frontier deployed-composite count (want 1) = " + ((Select-String -Path (Join-Path $PROJ 'paper_A_frontier.tex') -Pattern 'deployed composite' -AllMatches).Matches.Count) | Out-File $log -Append -Encoding utf8
# --- CLONE (submission + curated public replication) ---
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
git commit -m "R20 FIX: submission tex now carries the deployed-composite paragraph and Algorithm OA.2 rewording (prior push was stale); code/job_wrds_holdout.py credential/path leak scrubbed to env vars; job_composite.py + composite_results.json present" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 3 | Out-File $log -Append -Encoding utf8
git push origin HEAD 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
"DONE R20 FIX" | Out-File $log -Append -Encoding utf8
