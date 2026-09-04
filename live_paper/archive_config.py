# archive_config.py — shared config for the option-chain archive jobs.
# The archive is a RESEARCH DATA CAPTURE, fully independent of the pre-registered
# live trading signal (live_signal.py / top-100 book). Nothing here changes what we trade.
import os

# ---- storage roots -----------------------------------------------------------
# Primary write target = the Box Drive mount (streams to Box cloud, so it's the durable
# store AND keeps the near-full C: partition light). Box mounts at %USERPROFILE%\Box.
# Override with env CHAIN_ARCHIVE_ROOT if the mount ever moves.
ARCHIVE_ROOT = os.environ.get(
    "CHAIN_ARCHIVE_ROOT",
    os.path.join(os.path.expanduser("~"), "Box", "GBC_data", "chain_archive"))

# Optional extra mirror. Not needed with a cloud-streaming primary (Box already IS the
# off-machine copy), so left blank. Set to a local path to also robocopy there.
DRIVE_MIRROR = os.environ.get("CHAIN_ARCHIVE_DRIVE", "")

UNIVERSE_DIR = os.path.join(ARCHIVE_ROOT, "_universe")
DATA_DIR     = ARCHIVE_ROOT  # daily EOD partitions land as ARCHIVE_ROOT/date=YYYY-MM-DD/
INTRADAY_DIR = os.path.join(ARCHIVE_ROOT, "intraday")  # intraday/date=YYYY-MM-DD/snap-HHMM.parquet

# ---- intraday watchlist (small N, snapshotted ~every 15 min through the session) ----
# Free feed is ~15-min delayed, so 15-min cadence is the meaningful max resolution.
# Kept small so a full pass finishes fast. Edit _universe/watchlist.csv to change it
# (one ticker per line, header 'ticker'); if that file is absent this default is written.
WATCHLIST_DEFAULT = [
    # index / vol / rate / sector ETFs
    "SPY", "QQQ", "IWM", "DIA", "VXX", "UVXY", "TLT", "HYG", "GLD", "SLV", "USO", "UNG",
    "XLF", "XLE", "XLK", "SMH", "EEM", "FXI",
    # mega/high-liquidity single names
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "AMD", "NFLX",
    "ORCL", "CRM", "JPM", "BAC", "WFC", "GS", "V", "MA", "XOM", "CVX",
    "UNH", "LLY", "COST", "WMT", "HD", "DIS", "PLTR", "COIN", "MSTR", "SMCI",
    "MU", "QCOM", "INTC", "BABA", "UBER", "SHOP", "NET", "SOFI", "HOOD", "CCL",
]

# ---- capture scope (per user decision 2026-07-27) ----------------------------
# Universe:  ALL optionable US names.  Depth: FULL chain (puts+calls, every
# strike, every listed expiry).  Retention: keep everything, zstd-compressed.
CAPTURE_RIGHTS   = ("puts", "calls")
PARQUET_COMPRESS = "zstd"
UNIVERSE_MAX_AGE_DAYS = 7      # rebuild optionable list if older than this

# ---- politeness / robustness -------------------------------------------------
MAX_WORKERS   = int(os.environ.get("CHAIN_ARCHIVE_WORKERS", "10"))
RETRIES       = 3
RETRY_BACKOFF = 1.7            # seconds, exponential
REQUEST_PAUSE = 0.0           # optional per-call sleep if Yahoo rate-limits

def ensure_dirs():
    os.makedirs(UNIVERSE_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(INTRADAY_DIR, exist_ok=True)

def load_watchlist():
    """Read _universe/watchlist.csv, creating it from WATCHLIST_DEFAULT on first use."""
    import csv
    path = os.path.join(UNIVERSE_DIR, "watchlist.csv")
    if not os.path.exists(path):
        os.makedirs(UNIVERSE_DIR, exist_ok=True)
        with open(path, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["ticker"])
            for t in WATCHLIST_DEFAULT:
                w.writerow([t])
        return list(WATCHLIST_DEFAULT)
    with open(path) as f:
        return [r["ticker"].strip() for r in csv.DictReader(f) if r.get("ticker", "").strip()]
