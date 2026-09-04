$ErrorActionPreference = 'Continue'
Set-Location 'C:\Users\OWNER\Claude\Projects\GBC Project'
$log = 'zz_reorg_log.txt'
"=== reorg.ps1 start $(Get-Date -Format o) ===" | Out-File $log -Append -Encoding utf8

# stale lock sweep
Get-ChildItem -Path '.git' -Recurse -Filter '*.lock' -File -ErrorAction SilentlyContinue |
  Where-Object { $_.LastWriteTime -lt (Get-Date).AddMinutes(-10) } |
  ForEach-Object { Remove-Item $_.FullName -Force }

git add -A 2>&1 | Out-Null
git commit -m "pre-reorg snapshot (ps1)" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 |
  Select-Object -First 3 | Out-File $log -Append -Encoding utf8

$keep = @('paper_A_frontier.tex','paper_A_frontier.pdf','refs_v3.bib','README.md',
          'RESEARCH_IDEAS_BACKLOG.md','START_RUNNER_CLICK_ME.bat','auto_runner.bat',
          '.gitignore','.gitattributes')
foreach ($d in 'paper','paper/archive_pdfs','code','results','logs','docs','figures','tools') {
  if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d | Out-Null }
}
$files = git ls-files | Where-Object { $_ -notmatch '/' -and ($keep -notcontains $_) }
$moved = 0
foreach ($f in $files) {
  $dest = $null
  if     ($f -match '\.py$')  { $dest = 'code' }
  elseif ($f -match '\.json$'){ $dest = 'results' }
  elseif ($f -match '\.png$') { $dest = 'figures' }
  elseif ($f -match '\.(txt|log)$') { $dest = 'logs' }
  elseif ($f -match '^(PaperA_|PaperB_|GRAFTQ_main|graftq).*\.pdf$') { $dest = 'paper/archive_pdfs' }
  elseif ($f -match '\.pdf$') { $dest = 'docs' }
  elseif ($f -match '\.tex$') { $dest = 'paper' }
  elseif ($f -match '\.(md|html)$') { $dest = 'docs' }
  elseif ($f -match '\.bat$') { $dest = 'tools' }
  if ($dest) {
    git mv -- "$f" "$dest/$f" 2>&1 | Out-Null
    "$f -> $dest/" | Out-File $log -Append -Encoding utf8
    $moved++
  } else {
    "$f (left in place)" | Out-File $log -Append -Encoding utf8
  }
}
"moved: $moved" | Out-File $log -Append -Encoding utf8

git add -A 2>&1 | Out-Null
git commit -m "Reorganize repository into folders; README links the live draft" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 |
  Select-Object -First 3 | Out-File $log -Append -Encoding utf8
git log -1 --oneline 2>&1 | Out-File $log -Append -Encoding utf8
git push origin master 2>&1 | Select-Object -Last 3 | Out-File $log -Append -Encoding utf8
git push origin +master:main 2>&1 | Select-Object -Last 3 | Out-File $log -Append -Encoding utf8
(git status --porcelain | Measure-Object -Line).Lines | Out-File $log -Append -Encoding utf8
"DONE" | Out-File $log -Append -Encoding utf8
