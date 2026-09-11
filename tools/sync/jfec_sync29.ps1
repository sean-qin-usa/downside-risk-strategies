$ErrorActionPreference='Continue'
$PROJ='C:\Users\OWNER\Claude\Projects\GBC Project'
$CLONE='C:\Users\OWNER\Claude\Projects\downside-risk-paper'
$log=Join-Path $PROJ 'zz_jfec_sync_log.txt'
"=== jfec_sync29 (R3: proposition + de-AI + fixes) $(Get-Date -Format o) ===" | Out-File $log -Encoding utf8
Set-Location $PROJ
if(Test-Path '.git\index.lock'){Remove-Item '.git\index.lock' -Force}
git add -A 2>&1 | Out-Null
git commit -m "R3: capstone Proposition (the score orders the frontier) with proof in the appendix; rename Conclusion and make limitations substantive (predictive, not a structural cause); fix J5 causal definition (t-5..t-1); regret 'quadratic' -> 'locally quadratic'; drop the 'only remaining free assumption' overclaim and correct 'by construction a departure' (a correct low-nu t can produce high realized kurtosis); note bias-corrected skew/kurt estimators; AI-prose de-verdicting throughout; Korea control kept" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
git push origin master 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
git push origin +master:main 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
Set-Location $CLONE
if(Test-Path '.git\index.lock'){Remove-Item '.git\index.lock' -Force}
git pull 2>&1 | Out-Null
foreach($f in 'paper_A_jfec.pdf','paper_A_jfec.tex','paper_A_jfec_online_appendix.pdf','paper_A_jfec_online_appendix.tex'){Copy-Item (Join-Path $PROJ $f) 'submission\' -Force}
foreach($f in 'paper_A_frontier.pdf','paper_A_frontier.tex'){Copy-Item (Join-Path $PROJ $f) '.' -Force}
git add -A 2>&1 | Out-Null
git commit -m "R3: capstone proposition + proof; Conclusion rename + substantive limitations; J5 definition fix; locally-quadratic regret; overclaim fixes; skew/kurt note; AI-prose pass; both builds and OA" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
git push origin HEAD 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
"DONE R3" | Out-File $log -Append -Encoding utf8
