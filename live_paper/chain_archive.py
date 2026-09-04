# chain_archive.py — DAILY full option-chain archive for ALL optionable US names.
# Captures every strike, both rights (puts+calls), every listed expiry, with quotes + greeks
# proxies (IV, volume, OI). Written as zstd-compressed parquet partitioned by date so it can
# be queried later for arbitrary strategy research. Independent of the live trading signal.
#
# Storage layout:
#   <ARCHIVE_ROOT>/date=YYYY-MM-DD/part-00001.parquet, part-00002.parquet, ...
#   <ARCHIVE_ROOT>/date=YYYY-MM-DD/_manifest.json
#   <ARCHIVE_ROOT>/date=YYYY-MM-DD/_done_tickers.txt   (checkpoint -> resumable)
#
# Run:  python chain_archive.py            (archive TODAY, resume if partially done)
#       python chain_archive.py --date 2026-07-27
# NOTE: this is a heavy, long-running job (all optionable names x full chain). Schedule it
# AFTER the close, off the critical path of the morning trading-signal job.
import os, sys, csv, json, time, datetime as dt

# --- auto_runner watchdog (added 2026-09-03 by Claude; same block as intraday_watchlist) ---
try:
    import subprocess as _sp
    _hb = r"C:\Users\OWNER\Claude\Projects\GBC Project\autojobs\_heartbeat.txt"
    _ar = r"C:\Users\OWNER\Claude\Projects\GBC Project\auto_runner.bat"
    if (not os.path.exists(_hb)) or (time.time() - os.path.getmtime(_hb) > 300):
        _sp.Popen('start "gbc_auto_runner" /min cmd /c "%s"' % _ar, shell=True)
        with open(r"C:\Users\OWNER\Claude\Projects\GBC Project\autojobs\_watchdog_log.txt", "a") as _f:
            _f.write("relaunched auto_runner (chain_archive) at %s\n" % dt.datetime.now())
except Exception:
    pass
# --- end watchdog ---
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import archive_config as C

try:
    import yfinance as yf
except ImportError:
    print("yfinance missing — pip install yfinance"); sys.exit(1)

BATCH_TICKERS = 200          # tickers per parquet part file
KEEP_COLS = ["contractSymbol", "strike", "lastPrice", "bid", "ask", "volume",
             "openInterest", "impliedVolatility", "inTheMoney", "lastTradeDate"]


def parse_args():
    d = dt.date.today()
    if "--date" in sys.argv:
        d = dt.datetime.strptime(sys.argv[sys.argv.index("--date") + 1], "%Y-%m-%d").date()
    return d


def load_universe():
    latest = os.path.join(C.UNIVERSE_DIR, "optionable_latest.csv")
    if not os.path.exists(latest):
        print("no optionable universe cache — run build_optionable_universe.py first"); sys.exit(1)
    with open(latest) as f:
        return [r["ticker"] for r in csv.DictReader(f) if r.get("ticker")]


def get_spot(tk):
    try:
        p = tk.fast_info.get("lastPrice") or tk.fast_info.get("last_price")
        if p:
            return float(p)
    except Exception:
        pass
    try:
        h = tk.history(period="5d")["Close"]
        return float(h.iloc[-1]) if len(h) else float("nan")
    except Exception:
        return float("nan")


def fetch_one(ticker, asof):
    """All strikes, both rights, all expiries for one name. Returns list[dict]."""
    tk = yf.Ticker(ticker)
    try:
        expiries = tk.options
    except Exception:
        return []
    if not expiries:
        return []
    spot = get_spot(tk)
    snap_ts = dt.datetime.now().isoformat(timespec="seconds")
    out = []
    for e in expiries:
        try:
            ed = dt.datetime.strptime(e, "%Y-%m-%d").date()
        except Exception:
            continue
        dte = (ed - asof).days
        chain = None
        for attempt in range(C.RETRIES):
            try:
                chain = tk.option_chain(e)
                break
            except Exception:
                time.sleep(C.RETRY_BACKOFF ** attempt)
        if chain is None:
            continue
        for right, df in (("P", chain.puts), ("C", chain.calls)):
            if df is None or len(df) == 0:
                continue
            sub = df[[c for c in KEEP_COLS if c in df.columns]].copy()
            sub.insert(0, "asof", str(asof))
            sub.insert(1, "snapshot_ts", snap_ts)
            sub.insert(2, "ticker", ticker)
            sub.insert(3, "right", right)
            sub.insert(4, "expiry", e)
            sub.insert(5, "dte", dte)
            sub["spot"] = spot
            out.extend(sub.to_dict("records"))
        if C.REQUEST_PAUSE:
            time.sleep(C.REQUEST_PAUSE)
    return out


def load_done(done_path):
    if not os.path.exists(done_path):
        return set()
    with open(done_path) as f:
        return {ln.strip() for ln in f if ln.strip()}


def flush(rows, out_dir, part_idx):
    if not rows:
        return part_idx
    df = pd.DataFrame(rows)
    path = os.path.join(out_dir, f"part-{part_idx:05d}.parquet")
    df.to_parquet(path, compression=C.PARQUET_COMPRESS, index=False)
    print(f"  wrote {len(df):,} rows -> {os.path.basename(path)}")
    return part_idx + 1


def main():
    C.ensure_dirs()
    asof = parse_args()
    out_dir = os.path.join(C.DATA_DIR, f"date={asof}")
    os.makedirs(out_dir, exist_ok=True)
    done_path = os.path.join(out_dir, "_done_tickers.txt")

    universe = load_universe()
    done = load_done(done_path)
    todo = [t for t in universe if t not in done]
    # resume part index past any existing parts
    existing_parts = [f for f in os.listdir(out_dir) if f.startswith("part-") and f.endswith(".parquet")]
    part_idx = (max([int(f[5:10]) for f in existing_parts]) + 1) if existing_parts else 1

    print(f"archive {asof}: {len(universe)} optionable, {len(done)} already done, {len(todo)} to go")
    t0 = time.time()
    rows, batch_syms, n_done, total_rows = [], [], 0, 0

    with open(done_path, "a", buffering=1) as df_done, \
         ThreadPoolExecutor(max_workers=C.MAX_WORKERS) as ex:
        futs = {ex.submit(fetch_one, t, asof): t for t in todo}
        for fut in as_completed(futs):
            t = futs[fut]
            try:
                r = fut.result()
            except Exception:
                r = []
            rows.extend(r)
            total_rows += len(r)
            batch_syms.append(t)
            df_done.write(t + "\n")
            n_done += 1
            if len(batch_syms) >= BATCH_TICKERS:
                part_idx = flush(rows, out_dir, part_idx)
                rows, batch_syms = [], []
                print(f"  progress {n_done}/{len(todo)}  rows={total_rows:,}  "
                      f"({(time.time()-t0)/60:.1f} min)")
        part_idx = flush(rows, out_dir, part_idx)

    # size accounting
    nbytes = sum(os.path.getsize(os.path.join(out_dir, f))
                 for f in os.listdir(out_dir) if f.endswith(".parquet"))
    manifest = dict(asof=str(asof), n_optionable=len(universe), n_captured=len(done) + n_done,
                    rows_this_run=total_rows, parquet_bytes=nbytes,
                    parquet_mb=round(nbytes / 1e6, 1), minutes=round((time.time() - t0) / 60, 1),
                    capture="full chain (puts+calls, all strikes/expiries)", compression=C.PARQUET_COMPRESS)
    with open(os.path.join(out_dir, "_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print("DONE", json.dumps(manifest))


if __name__ == "__main__":
    main()
