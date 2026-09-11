$ErrorActionPreference = 'Continue'
$PROJ = 'C:\Users\OWNER\Claude\Projects\GBC Project'
$CLONE = 'C:\Users\OWNER\Claude\Projects\downside-risk-paper'
$log = Join-Path $PROJ 'zz_txtpush_log.txt'
"=== txtpush $(Get-Date -Format o) ===" | Out-File $log -Encoding utf8
Set-Location $CLONE
git pull 2>&1 | Out-Null
if (-not (Test-Path 'docs')) { New-Item -ItemType Directory -Path 'docs' | Out-Null }
Copy-Item (Join-Path $PROJ 'paper_plain.txt') 'docs\paper_plain.txt' -Force
git add -A 2>&1 | Out-Null
git commit -m "Add plain-text render of the manuscript (accessibility / text-analysis tooling)" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
git push origin HEAD 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
"DONE" | Out-File $log -Append -Encoding utf8
