@echo off
cd /d "%~dp0"
python make_figures_v2.py > figures_run_log.txt 2>&1
type figures_run_log.txt
