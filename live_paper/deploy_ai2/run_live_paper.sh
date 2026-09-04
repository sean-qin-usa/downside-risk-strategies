#!/usr/bin/env bash
# GBC live paper pipeline — ai2 runner (cron-safe). Mirrors run_live_paper.bat.
# Layout on ai2: ~/gbc_live/{live_paper/{live_signal.py,settle_tickets.py}, forward_signals/}
set -u
BASE="$HOME/gbc_live"
cd "$BASE" || exit 1
PY="$BASE/venv/bin/python"
if [ ! -x "$PY" ]; then
  python3 -m venv "$BASE/venv" && "$BASE/venv/bin/pip" -q install yfinance pandas numpy
fi
"$PY" -c "import yfinance" 2>/dev/null || "$BASE/venv/bin/pip" -q install yfinance pandas numpy
{
  echo "==== $(date '+%Y-%m-%d %H:%M:%S %Z') ===="
  "$PY" live_paper/live_signal.py
  "$PY" live_paper/settle_tickets.py
  echo "FIN_LIVE_PAPER"
} >> live_paper/live_paper_log.txt 2>&1
