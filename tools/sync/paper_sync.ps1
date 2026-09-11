$ErrorActionPreference = 'Continue'
$PROJ = 'C:\Users\OWNER\Claude\Projects\GBC Project'
$CLONE = 'C:\Users\OWNER\Claude\Projects\downside-risk-paper'
$log = Join-Path $PROJ 'zz_paper_sync_log.txt'
"=== paper_sync $(Get-Date -Format o) ===" | Out-File $log -Encoding utf8

# 1. clone or update
if (-not (Test-Path (Join-Path $CLONE '.git'))) {
  git clone https://github.com/sean-qin-usa/downside-risk-paper.git $CLONE 2>&1 | Select-Object -Last 2 | Out-File $log -Append -Encoding utf8
} else {
  Set-Location $CLONE; git pull 2>&1 | Select-Object -Last 2 | Out-File $log -Append -Encoding utf8
}
if (-not (Test-Path (Join-Path $CLONE '.git'))) { "CLONE FAILED" | Out-File $log -Append -Encoding utf8; exit 1 }
Set-Location $CLONE

# 2. copy the paper set (explicit, license-safe: pdf/tex/bib/md/py/json only)
Copy-Item (Join-Path $PROJ 'paper_A_frontier.pdf') . -Force
Copy-Item (Join-Path $PROJ 'paper_A_frontier.tex') . -Force
Copy-Item (Join-Path $PROJ 'refs_v3.bib') . -Force
foreach ($d in 'docs','code','results') { if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d | Out-Null } }
foreach ($f in 'COVER_LETTER_JFEC.md','JOURNAL_REQUIREMENTS_2026-09.md','LONG_ABSTRACT_SSRN.md','SUBMISSION_STRATEGY.md') {
  $src = Join-Path $PROJ "docs\$f"; if (Test-Path $src) { Copy-Item $src 'docs\' -Force }
  $srcR = Join-Path $PROJ $f;       if (Test-Path $srcR) { Copy-Item $srcR 'docs\' -Force }
}
$ap = Join-Path $PROJ 'docs\jfec_abstract_100w.tex'; if (Test-Path $ap) { Copy-Item $ap 'docs\' -Force }
$oa = Join-Path $PROJ 'paper\paper_A_online_appendix.tex'; if (Test-Path $oa) { Copy-Item $oa . -Force }
Copy-Item (Join-Path $PROJ 'code\*.py') 'code\' -Force -ErrorAction SilentlyContinue
Copy-Item (Join-Path $PROJ 'results\*.json') 'results\' -Force -ErrorAction SilentlyContinue
"copied paper set" | Out-File $log -Append -Encoding utf8

# 3. prepend paper section to README if absent (preserve existing content)
$rd = 'README.md'
$cur = if (Test-Path $rd) { Get-Content $rd -Raw } else { '' }
if ($cur -notmatch 'paper_A_frontier\.pdf') {
  $top = @"
# Downside Risk at the Misspecification Frontier

**The paper: [paper_A_frontier.pdf](paper_A_frontier.pdf)** ([LaTeX](paper_A_frontier.tex) | [bibliography](refs_v3.bib))

A real-time score for when nonparametric models beat industry-standard VaR and ES, with a deployable amortized engine. Sole-authored by Sean Qin; developed with the guidance of Prof. Wenxin Jiang (Northwestern). ``code/`` holds the study scripts, ``results/`` the derived statistics behind every number in the paper, ``docs/`` the submission material. No licensed data (CRSP/WRDS, Bloomberg) are redistributed; panels rebuild from the documented queries for licensed subscribers. Day-to-day working notes live in the companion repository ``downside-risk-strategies``.

---

"@
  ($top + $cur) | Set-Content $rd -Encoding utf8
  "README updated" | Out-File $log -Append -Encoding utf8
}

# 4. commit + push
git add -A 2>&1 | Out-Null
git commit -m "Add the paper: Downside Risk at the Misspecification Frontier (tex+pdf+bib), study code, derived results, submission docs" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
git push origin HEAD 2>&1 | Select-Object -Last 2 | Out-File $log -Append -Encoding utf8
git log -1 --oneline 2>&1 | Out-File $log -Append -Encoding utf8

# 5. cross-link from the strategies README (once)
Set-Location $PROJ
$srd = Get-Content 'README.md' -Raw
if ($srd -notmatch 'downside-risk-paper') {
  $srd = $srd -replace [regex]::Escape('The draft at the link above is the working version and is updated continuously; dated snapshots live in `paper/archive_pdfs/`.'),
    ('The draft at the link above is the working version and is updated continuously; dated snapshots live in `paper/archive_pdfs/`. The curated replication repository for the manuscript is [downside-risk-paper](https://github.com/sean-qin-usa/downside-risk-paper).')
  $srd | Set-Content 'README.md' -Encoding utf8
  git add README.md 2>&1 | Out-Null
  git commit -m "README: link the curated paper repository" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01PaysugvHD2tgCJvXLSscWa" 2>&1 | Select-Object -First 2 | Out-File $log -Append -Encoding utf8
  git push origin master 2>&1 | Select-Object -Last 2 | Out-File $log -Append -Encoding utf8
  git push origin +master:main 2>&1 | Select-Object -Last 2 | Out-File $log -Append -Encoding utf8
}
"DONE" | Out-File $log -Append -Encoding utf8
