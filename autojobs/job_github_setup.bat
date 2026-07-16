@echo off
set G=C:\Users\OWNER\Claude\Projects\GBC Project
cd /d "%G%"
echo === git / gh availability === > "%G%\github_setup.txt"
git --version >> "%G%\github_setup.txt" 2>&1
gh --version >> "%G%\github_setup.txt" 2>&1
echo === gh auth status === >> "%G%\github_setup.txt"
gh auth status >> "%G%\github_setup.txt" 2>&1
echo === init repo (code+docs+results only; big data ignored) === >> "%G%\github_setup.txt"
if not exist .git git init >> "%G%\github_setup.txt" 2>&1
> .gitignore echo *.csv
>> .gitignore echo *.csv.gz
>> .gitignore echo *.parquet
>> .gitignore echo *.pkl
>> .gitignore echo *.gz
>> .gitignore echo autojobs/done/
>> .gitignore echo __pycache__/
>> .gitignore echo mh_quantiles*.csv
>> .gitignore echo samerows_merged.csv
git add *.py *.md *.json *.png .gitignore autojobs/*.py autojobs/*.bat >> "%G%\github_setup.txt" 2>&1
git -c user.email=qinfamily2025@gmail.com -c user.name="Sean Qin" commit -m "GBC research snapshot: VRP strategies, IQN/amortization, regime detector, reusable tooling" >> "%G%\github_setup.txt" 2>&1
echo === current remotes === >> "%G%\github_setup.txt"
git remote -v >> "%G%\github_setup.txt" 2>&1
git log --oneline -1 >> "%G%\github_setup.txt" 2>&1
echo DONE_GITHUB >> "%G%\github_setup.txt"
