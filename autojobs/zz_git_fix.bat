@echo off
set G=C:\Users\OWNER\Claude\Projects\GBC Project
cd /d "%G%"
echo === GIT FIX %date% %time% === > "%G%\git_fix_done.txt"
git config user.email "qinfamily2025@gmail.com" >> "%G%\git_fix_done.txt" 2>&1
git config user.name "Sean Qin" >> "%G%\git_fix_done.txt" 2>&1
git add -A >> "%G%\git_fix_done.txt" 2>&1
git commit -m "GBC research 2026-07-20: misspec frontier + FRTB battery (CAViaR/EVT/Kupiec/Christoffersen/DM/MCS) + Heston SBC + Bloomberg cross-asset (FX/Korea/countries/universal) with significance + thesis-alignment memo" >> "%G%\git_fix_done.txt" 2>&1
echo --- local commit log --- >> "%G%\git_fix_done.txt"
git log --oneline -3 >> "%G%\git_fix_done.txt" 2>&1
echo --- existing remotes --- >> "%G%\git_fix_done.txt"
git remote -v >> "%G%\git_fix_done.txt" 2>&1
echo --- add origin if missing (private strategies repo) --- >> "%G%\git_fix_done.txt"
git remote add origin https://github.com/sean-qin-usa/downside-risk-strategies.git >> "%G%\git_fix_done.txt" 2>&1
echo --- attempt NON-FORCE push (safe: rejected if diverged) --- >> "%G%\git_fix_done.txt"
git push origin HEAD >> "%G%\git_fix_done.txt" 2>&1
echo === DONE %date% %time% === >> "%G%\git_fix_done.txt"
