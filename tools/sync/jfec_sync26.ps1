$ErrorActionPreference='Continue'
$PROJ='C:\Users\OWNER\Claude\Projects\GBC Project'
$CLONE='C:\Users\OWNER\Claude\Projects\downside-risk-paper'
$log=Join-Path $PROJ 'zz_jfec_sync_log.txt'
"=== jfec_sync26 (JFEC-ification) $(Get-Date -Format o) ===" | Out-File $log -Encoding utf8
Set-Location $PROJ
if(Test-Path '.git\index.lock'){Remove-Item '.git\index.lock' -Force}
git add -A 2>&1 | Out-Null
git commit -m "JFEC-ification: unnumbered introduction (OUP house style); Contributions subsection dissolved into three-literatures prose (frontier first); sections renamed (Related literature and benchmark models / Semiparametric VaR and ES model / Extensions and implications); end-of-intro roadmap; reporting-conventions scaffolding and standard-test glosses (Kupiec/Christoffersen/DM/MCS) removed; engine->estimator in the formal sections; two-author title block with shared affiliation; figure alt text; submission text ends p41" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
git push origin master 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
git push origin +master:main 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
Set-Location $CLONE
if(Test-Path '.git\index.lock'){Remove-Item '.git\index.lock' -Force}
git pull 2>&1 | Out-Null
foreach($f in 'paper_A_jfec.pdf','paper_A_jfec.tex'){Copy-Item (Join-Path $PROJ $f) 'submission\' -Force}
foreach($f in 'paper_A_frontier.pdf','paper_A_frontier.tex','refs_v3.bib'){Copy-Item (Join-Path $PROJ $f) '.' -Force}
git add -A 2>&1 | Out-Null
git commit -m "JFEC-ification: unnumbered intro, prose contributions, renamed sections, roadmap, de-refereed intro, two-author title block; submission and reading copy both updated" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
git push origin HEAD 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
"DONE JFEC-ification" | Out-File $log -Append -Encoding utf8
