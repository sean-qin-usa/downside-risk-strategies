$ErrorActionPreference = 'Continue'
$PROJ = 'C:\Users\OWNER\Claude\Projects\GBC Project'
$CLONE = 'C:\Users\OWNER\Claude\Projects\downside-risk-paper'
$log = Join-Path $PROJ 'zz_paper_tidy_log.txt'
"=== paper_tidy $(Get-Date -Format o) ===" | Out-File $log -Encoding utf8
Set-Location $CLONE
git pull 2>&1 | Select-Object -Last 1 | Out-File $log -Append -Encoding utf8
$keep = @('README.md','paper_A_frontier.pdf','paper_A_frontier.tex','paper_A_online_appendix.tex','refs_v3.bib','.gitignore','.gitattributes','LICENSE')
foreach ($d in 'code','results','figures','docs') { if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d | Out-Null } }
$files = git ls-files | Where-Object { $_ -notmatch '/' -and ($keep -notcontains $_) }
foreach ($f in $files) {
  $dest = $null
  if     ($f -match '\.py$')   { $dest = 'code' }
  elseif ($f -match '\.json$') { $dest = 'results' }
  elseif ($f -match '\.(png|jpg|pdf)$' -and $f -notmatch '^paper_') { $dest = 'figures' }
  elseif ($f -match '\.(md|txt)$') { $dest = 'docs' }
  if ($dest) { git mv -- "$f" "$dest/$f" 2>&1 | Out-Null; "$f -> $dest/" | Out-File $log -Append -Encoding utf8 }
  else { "$f (left)" | Out-File $log -Append -Encoding utf8 }
}
git add -A 2>&1 | Out-Null
git commit -m "Tidy: move study scripts to code/, derived results to results/, images to figures/" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
git push origin HEAD 2>&1 | Select-Object -Last 2 | Out-File $log -Append -Encoding utf8
git log -1 --oneline 2>&1 | Out-File $log -Append -Encoding utf8
"DONE" | Out-File $log -Append -Encoding utf8
