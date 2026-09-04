$ErrorActionPreference = 'Continue'
$PROJ = 'C:\Users\OWNER\Claude\Projects\GBC Project'
$CLONE = 'C:\Users\OWNER\Claude\Projects\downside-risk-paper'
$log = Join-Path $PROJ 'zz_jfec_sync_log.txt'
"=== jfec_sync3 $(Get-Date -Format o) ===" | Out-File $log -Encoding utf8
Set-Location $PROJ
git add -A 2>&1 | Out-Null
git commit -m "One-paper framing: program footnote replaced, all companion-paper references and internal TODOs removed from sources; submission-format README added" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
git push origin master 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
git push origin +master:main 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
Set-Location $CLONE
git pull 2>&1 | Out-Null
if (-not (Test-Path 'submission')) { New-Item -ItemType Directory -Path 'submission' | Out-Null }
foreach ($f in 'paper_A_jfec.pdf','paper_A_jfec.tex','paper_A_jfec_online_appendix.pdf','paper_A_jfec_online_appendix.tex') {
  Copy-Item (Join-Path $PROJ $f) 'submission\' -Force
}
foreach ($f in 'paper_A_frontier.pdf','paper_A_frontier.tex','refs_v3.bib','README.md') {
  Copy-Item (Join-Path $PROJ $f) '.' -Force
}
Copy-Item (Join-Path $PROJ 'docs\TUNING_GRID_PREREG.md') '.' -Force
Copy-Item (Join-Path $PROJ 'submission_README.md') 'submission\README.md' -Force
git add -A 2>&1 | Out-Null
git commit -m "Self-contained framing: companion references removed; submission folder README explains journal format" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
git push origin HEAD 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
"DONE" | Out-File $log -Append -Encoding utf8
