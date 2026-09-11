$ErrorActionPreference = 'Continue'
$PROJ = 'C:\Users\OWNER\Claude\Projects\GBC Project'
$CLONE = 'C:\Users\OWNER\Claude\Projects\downside-risk-paper'
$log = Join-Path $PROJ 'zz_paper_final_log.txt'
"=== paper_final_sync $(Get-Date -Format o) ===" | Out-File $log -Encoding utf8

# 1. strategies repo: commit + push tonight's swept paper and docs
Set-Location $PROJ
powershell -NoProfile -Command "Get-ChildItem -Path '.git' -Recurse -Filter '*.lock' -File -ErrorAction SilentlyContinue | Where-Object {$_.LastWriteTime -lt (Get-Date).AddMinutes(-10)} | ForEach-Object { Remove-Item $_.FullName -Force }" | Out-Null
git add -A 2>&1 | Out-Null
git commit -m "Metaphor sweep (ledger/dial/geography/harvest to journal language); structure comparison + ChatGPT review prompt in docs" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
git push origin master 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
git push origin +master:main 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8

# 2. paper repo: clean README (byte copy, no re-encoding), current paper files, push
Set-Location $CLONE
git pull 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
Copy-Item (Join-Path $PROJ 'README_paper_repo.md') (Join-Path $CLONE 'README.md') -Force
Copy-Item (Join-Path $PROJ 'paper_A_frontier.pdf') $CLONE -Force
Copy-Item (Join-Path $PROJ 'paper_A_frontier.tex') $CLONE -Force
Copy-Item (Join-Path $PROJ 'refs_v3.bib') $CLONE -Force
Copy-Item (Join-Path $PROJ 'docs\STRUCTURE_COMPARISON_JFEC.md') (Join-Path $CLONE 'docs\') -Force -ErrorAction SilentlyContinue
git add -A 2>&1 | Out-Null
git commit -m "Clean README (fix encoding, drop private-repo link); sync current draft" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
git push origin HEAD 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
git log -1 --oneline 2>&1 | Out-File $log -Append -Encoding utf8
"DONE" | Out-File $log -Append -Encoding utf8
