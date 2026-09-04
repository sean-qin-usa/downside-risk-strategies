# build_optionable_universe.py — build/refresh the list of ALL optionable US symbols.
# Source of listings: NASDAQ Trader public symbol directories (nasdaqlisted + otherlisted),
# which enumerate every US-listed equity/ETF. We then probe each with yfinance and keep the
# ones that actually have a listed option chain. Result is cached and reused daily by
# chain_archive.py; rebuild weekly (cheap relative to the daily full-chain pull).
#
# Run:  python build_optionable_universe.py           (skips if cache is fresh)
#       python build_optionable_universe.py --force    (always rebuild)
# Resumable: probed symbols are checkpointed, so an interrupted run resumes.
import os, sys, io, csv, time, json, datetime as dt, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import archive_config as C

NASDAQ_LISTED = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED  = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
TODAY = dt.date.today()

try:
    import yfinance as yf
except ImportError:
    print("yfinance missing — pip install yfinance"); sys.exit(1)


def _fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def list_all_symbols():
    """Return the raw set of candidate tickers from both NASDAQ Trader directories."""
    syms = set()
    for url, sym_col, test_col, etf_col in [
        (NASDAQ_LISTED, "Symbol", "Test Issue", "ETF"),
        (OTHER_LISTED,  "ACT Symbol", "Test Issue", "ETF"),
    ]:
        txt = _fetch(url)
        lines = [ln for ln in txt.splitlines() if ln and not ln.startswith("File Creation Time")]
        rdr = csv.DictReader(lines, delimiter="|")
        for row in rdr:
            s = (row.get(sym_col) or "").strip()
            if not s:
                continue
            if (row.get(test_col) or "").strip() == "Y":       # drop test issues
                continue
            if any(ch in s for ch in "$^"):                     # drop pfd/warrant/unit oddities
                continue
            # yfinance uses '-' for share-class dots (BRK.B -> BRK-B)
            syms.add(s.replace(".", "-"))
    return sorted(syms)


def is_optionable(sym):
    """True if the symbol has at least one listed option expiry."""
    for attempt in range(C.RETRIES):
        try:
            opts = yf.Ticker(sym).options
            return bool(opts)
        except Exception:
            time.sleep(C.RETRY_BACKOFF ** attempt)
    return False


def _load_checkpoint(path):
    done = {}
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                s, v = line.rstrip("\n").split(",")
                done[s] = v == "1"
    return done


def main():
    C.ensure_dirs()
    force = "--force" in sys.argv
    latest = os.path.join(C.UNIVERSE_DIR, "optionable_latest.csv")

    # skip if cache is fresh enough
    if not force and os.path.exists(latest):
        age = (TODAY - dt.date.fromtimestamp(os.path.getmtime(latest))).days
        if age < C.UNIVERSE_MAX_AGE_DAYS:
            print(f"universe cache is {age}d old (< {C.UNIVERSE_MAX_AGE_DAYS}) -> reuse {latest}")
            return

    print("fetching NASDAQ Trader symbol directories ...")
    candidates = list_all_symbols()
    print(f"{len(candidates)} raw listed symbols to probe for options")

    ckpt = os.path.join(C.UNIVERSE_DIR, f"_probe_ckpt_{TODAY}.csv")
    done = _load_checkpoint(ckpt)
    todo = [s for s in candidates if s not in done]
    print(f"{len(done)} already probed, {len(todo)} to go")

    optionable = [s for s, ok in done.items() if ok]
    t0 = time.time()
    with open(ckpt, "a", buffering=1) as cf, \
         ThreadPoolExecutor(max_workers=C.MAX_WORKERS) as ex:
        futs = {ex.submit(is_optionable, s): s for s in todo}
        n = 0
        for fut in as_completed(futs):
            s = futs[fut]
            ok = False
            try:
                ok = fut.result()
            except Exception:
                ok = False
            cf.write(f"{s},{1 if ok else 0}\n")
            if ok:
                optionable.append(s)
            n += 1
            if n % 250 == 0:
                print(f"  probed {n}/{len(todo)}  optionable so far={len(optionable)}  "
                      f"({(time.time()-t0)/60:.1f} min)")

    optionable = sorted(set(optionable))
    dated = os.path.join(C.UNIVERSE_DIR, f"optionable_{TODAY}.csv")
    for path in (dated, latest):
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ticker"])
            for s in optionable:
                w.writerow([s])
    meta = dict(asof=str(TODAY), n_listed=len(candidates), n_optionable=len(optionable),
                minutes=round((time.time() - t0) / 60, 1))
    with open(os.path.join(C.UNIVERSE_DIR, "optionable_latest_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(f"DONE: {len(optionable)} optionable of {len(candidates)} listed -> {latest}")
    print(json.dumps(meta))


if __name__ == "__main__":
    main()
