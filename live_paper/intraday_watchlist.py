# intraday_watchlist.py — ONE intraday snapshot of the watchlist's full option chains.
# Cadence comes from the scheduler firing this repeatedly (~every 15 min) during market hours;
# each invocation writes a single timestamped snapshot, so runs are independent and cheap.
#
# NOTE: free yfinance quotes are ~15-min delayed, so 15-min cadence is the meaningful maximum
# resolution — snapshotting faster just recaptures the same delayed values. snapshot_ts is the
# wall-clock capture time (the underlying quotes lag it by the vendor delay).
#
# Output: <ARCHIVE_ROOT>/intraday/date=YYYY-MM-DD/snap-HHMM.parquet
# Run:    python intraday_watchlist.py            (snapshot now)
#         python intraday_watchlist.py --force     (ignore the market-hours guard)
import os, sys, json, time, datetime as dt

# --- auto_runner watchdog (added 2026-09-03 by Claude, per Sean: "run everything") ---
# If the autojobs runner heartbeat is missing or stale (>5 min), relaunch auto_runner.bat
# detached. This piggybacks on the Task Scheduler firing of this script (~every 15 min),
# so the runner self-heals after reboots/crashes. Remove this block to disable.
try:
    import subprocess as _sp
    _hb = r"C:\Users\OWNER\Claude\Projects\GBC Project\autojobs\_heartbeat.txt"
    _ar = r"C:\Users\OWNER\Claude\Projects\GBC Project\auto_runner.bat"
    if (not os.path.exists(_hb)) or (time.time() - os.path.getmtime(_hb) > 300):
        _sp.Popen('start "gbc_auto_runner" /min cmd /c "%s"' % _ar, shell=True)
        with open(r"C:\Users\OWNER\Claude\Projects\GBC Project\autojobs\_watchdog_log.txt", "a") as _f:
            _f.write("relaunched auto_runner at %s\n" % dt.datetime.now())
except Exception:
    pass
# --- end watchdog ---
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import archive_config as C
from chain_archive import fetch_one   # reuse the full-chain puller

try:
    import yfinance as yf  # noqa: F401  (imported for the clear error if missing)
except ImportError:
    print("yfinance missing — pip install yfinance"); sys.exit(1)


def market_open_now():
    """Rough US cash-session guard in America/New_York; weekdays 09:30–16:00.
    Holidays are not special-cased (a holiday just yields a near-static snapshot)."""
    try:
        from zoneinfo import ZoneInfo
        now = dt.datetime.now(ZoneInfo("America/New_York"))
    except Exception:
        now = dt.datetime.now()  # fall back to local time
    if now.weekday() >= 5:
        return False
    t = now.time()
    return dt.time(9, 30) <= t <= dt.time(16, 0)


def main():
    C.ensure_dirs()
    force = "--force" in sys.argv
    if not force and not market_open_now():
        print("market closed — skipping intraday snapshot (use --force to override)")
        return

    watch = C.load_watchlist()
    asof = dt.date.today()
    stamp = dt.datetime.now().strftime("%H%M")
    out_dir = os.path.join(C.INTRADAY_DIR, f"date={asof}")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"snap-{stamp}.parquet")
    if os.path.exists(out_path):
        print(f"snapshot {out_path} already exists — skip"); return

    t0 = time.time()
    rows = []
    with ThreadPoolExecutor(max_workers=C.MAX_WORKERS) as ex:
        futs = {ex.submit(fetch_one, t, asof): t for t in watch}
        for fut in as_completed(futs):
            try:
                rows.extend(fut.result())
            except Exception:
                pass

    if not rows:
        print("no rows captured (feed issue?) — nothing written"); return
    df = pd.DataFrame(rows)
    df.to_parquet(out_path, compression=C.PARQUET_COMPRESS, index=False)
    meta = dict(asof=str(asof), snap=stamp, n_watch=len(watch),
                n_names=int(df["ticker"].nunique()), rows=len(df),
                mb=round(os.path.getsize(out_path) / 1e6, 2),
                seconds=round(time.time() - t0, 1))
    print("SNAP", json.dumps(meta), "->", out_path)


if __name__ == "__main__":
    main()
