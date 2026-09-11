$ErrorActionPreference = 'Continue'
$PROJ = 'C:\Users\OWNER\Claude\Projects\GBC Project'
$CLONE = 'C:\Users\OWNER\Claude\Projects\downside-risk-paper'
$log = Join-Path $PROJ 'zz_paper_sync2_log.txt'
"=== paper_sync2 $(Get-Date -Format o) ===" | Out-File $log -Encoding utf8
$un = git -C $PROJ config user.name
$ue = git -C $PROJ config user.email
if (-not $un) { $un = 'Sean Qin' }
if (-not $ue) { $ue = 'qinfamily2025@gmail.com' }
"identity: $un <$ue>" | Out-File $log -Append -Encoding utf8
Set-Location $CLONE
git config user.name  "$un"
git config user.email "$ue"
git add -A 2>&1 | Out-Null
git commit -m "Add the paper: Downside Risk at the Misspecification Frontier (tex+pdf+bib), study code, derived results, submission docs" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 3 | Out-File $log -Append -Encoding utf8
git push origin HEAD 2>&1 | Select-Object -Last 2 | Out-File $log -Append -Encoding utf8
git log -1 --oneline 2>&1 | Out-File $log -Append -Encoding utf8
git ls-files | Measure-Object -Line | Out-File $log -Append -Encoding utf8
"DONE" | Out-File $log -Append -Encoding utf8
