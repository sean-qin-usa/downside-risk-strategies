# Run the live paper pipeline on ai2 (always-on) — setup

One-time, ~5 minutes. After this, data collection never depends on the Windows PC being awake.

## 1. Copy the files to ai2 (paste in Cygwin/Git Bash on this PC)
```bash
ssh steveqin@ai2 "mkdir -p ~/gbc_live/live_paper ~/gbc_live/forward_signals"
cd "/c/Users/OWNER/Claude/Projects/GBC Project"
scp live_paper/live_signal.py live_paper/settle_tickets.py steveqin@ai2:~/gbc_live/live_paper/
scp live_paper/deploy_ai2/run_live_paper.sh steveqin@ai2:~/gbc_live/
scp forward_signals/live_*.csv forward_signals/live_*_meta.json steveqin@ai2:~/gbc_live/forward_signals/ 2>/dev/null
ssh steveqin@ai2 "chmod +x ~/gbc_live/run_live_paper.sh && ~/gbc_live/run_live_paper.sh && tail -5 ~/gbc_live/live_paper/live_paper_log.txt"
```
The last command does a live test run — you should see `DONE <date> books: ...` and `SETTLE DONE`.
(Copying today's live_* files first prevents duplicate monthly tickets for July.)

## 2. Schedule it (cron on ai2)
First check ai2's timezone: `ssh steveqin@ai2 timedatectl | grep zone`
- If **America/New_York**: `crontab -e` and add: `20 9 * * 1-5 ~/gbc_live/run_live_paper.sh`
- If **UTC**: use `20 13 * * 1-5` (9:20 ET during daylight time; change to `20 14` when DST ends in November — or just set the box to NY time: `sudo timedatectl set-timezone America/New_York`).

## 3. Pull results to this PC (already automated)
`fetch_live_from_ai2.bat` (in the GBC Project folder) pulls ai2's forward_signals + logs into the project folder so the Claude verification tasks can see them. Point the existing Windows job at it OR run it manually — the Windows job (`GBC_LivePaperCheck`) can keep running too: the scripts skip generation when the pulled logs already contain today's/this month's entry, and if ai2 is ever down the Windows job acts as backup generator.

## Notes
- Canonical data lives on ai2 once this is set up; the PC copy is a mirror.
- Mac alternative: same scripts + `launchd`/cron work fine, but a laptop that sleeps has the same wake problem — ai2 is the right host.
- Nothing here sends orders; tickets remain a paper record.
