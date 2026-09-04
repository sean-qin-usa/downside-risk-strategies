#!/usr/bin/env bash
# Runs ON ai2: finalize install — permissions, first live run, cron registration. Idempotent.
set -u
BASE="$HOME/gbc_live"
chmod +x "$BASE/run_live_paper.sh"
echo "--- timezone:"; timedatectl show -p Timezone --value 2>/dev/null || cat /etc/timezone 2>/dev/null || date +%Z
TZNAME=$(timedatectl show -p Timezone --value 2>/dev/null || cat /etc/timezone 2>/dev/null || echo unknown)
if [ "$TZNAME" = "America/New_York" ]; then CRON="20 9 * * 1-5 $BASE/run_live_paper.sh"
else CRON="20 13 * * 1-5 $BASE/run_live_paper.sh   # 9:20am ET while EDT; shift to 14:20 when DST ends"
fi
( crontab -l 2>/dev/null | grep -v run_live_paper.sh ; echo "$CRON" ) | crontab -
echo "--- crontab installed:"; crontab -l | grep run_live_paper
echo "--- first live run (venv build + ~110 names, takes several minutes)..."
"$BASE/run_live_paper.sh"
echo "--- log tail:"; tail -12 "$BASE/live_paper/live_paper_log.txt"
echo "SETUP_REMOTE_DONE"
