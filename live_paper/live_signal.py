# live_signal.py — LIVE-DATA forward paper-trade signal generator (yfinance, free delayed)
# Books: weekly single-name VRP (Mon), monthly single-name VRP (1st signal day of month),
#        cross-asset ETF sleeve (1st signal day of month).
# Spec source: strategy_research_state.md §5b/8a/8b + TRADEABLE_STRATEGIES_CATALOGUE.md.
# Output: forward_signals/live_{book}_{date}.csv (+ _meta.json), append to live_{book}_forward_log.csv
# NO ORDERS ARE SENT. Tickets are a paper record; a human decides.
import os, sys, json, math, datetime as dt
import pandas as pd, numpy as np

try:
    import yfinance as yf
except ImportError:
    print("yfinance missing — run: pip install yfinance"); sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "forward_signals")
os.makedirs(OUT, exist_ok=True)

# ---------------- universe (top-100-liquid proxy; mirrors the WRDS top-100 book) ----------
NAMES = """AAPL MSFT NVDA AMZN GOOGL META TSLA AVGO AMD NFLX ORCL CRM ADBE COST WMT JPM BAC WFC GS MS
C V MA XOM CVX COP UNH LLY JNJ PFE MRK ABBV BMY TMO INTC MU QCOM TXN AMAT LRCX KLAC ASML SMCI PLTR
UBER ABNB SHOP PYPL COIN MSTR HOOD SOFI DKNG CCL RCL AAL UAL DAL LUV F GM RIVN LCID NIO XPEV LI
BABA JD PDD BIDU DIS CMCSA T VZ TMUS KO PEP MCD SBUX NKE LULU TGT HD LOW M CLF FCX NEM AA
BA CAT DE GE HON MMM UPS FDX DOCU ZM SNOW CRWD PANW NET DDOG MDB OKTA ROKU"""
# pruned 2026-07-21: GPS/SQ/X delisted per first live run
UNIVERSE = sorted(set(NAMES.split()))
# FXE has no tradeable delta-band puts (first live run); UUP added as the liquid USD/FX sleeve.
# FXE kept in list — script skips it gracefully; remove after a month if still unfillable.
ETF_SLEEVES = ["QQQ", "TLT", "GLD", "USO", "UNG", "FXE", "UUP", "HYG"]

# ---------------- fixed spec (pre-registered; do NOT tune here) ---------------------------
DELTA_TGT   = -0.12
TOP_PCT     = 0.10          # cross-sectional VRP selection, single-name books
RV_WIN      = 21            # trailing realized-vol window (trading days)
DTE_WEEKLY  = (5, 15)
DTE_MONTHLY = (20, 40)
DERISK_MULT = 0.5           # after a down period (sign, not magnitude)
RISK_FREE   = 0.04
MIN_PREM    = 0.05          # skip quotes with mid < $0.05 (untradeable)

TODAY = dt.date.today()

def norm_cdf(x): return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def put_delta(S, K, iv, T):
    if S <= 0 or K <= 0 or iv <= 0 or T <= 0: return np.nan
    d1 = (math.log(S / K) + (RISK_FREE + 0.5 * iv * iv) * T) / (iv * math.sqrt(T))
    return norm_cdf(d1) - 1.0

def trailing_rv(closes, win=RV_WIN):
    r = np.log(closes / closes.shift(1)).dropna().tail(win)
    if len(r) < win - 2: return np.nan
    return float(r.std(ddof=1) * math.sqrt(252))

def pick_put(tk, spot, dte_lo, dte_hi):
    """Nearest-to-target-delta put with a real market, within the DTE window."""
    best = None
    try: expiries = tk.options
    except Exception: return None
    for e in expiries:
        ed = dt.datetime.strptime(e, "%Y-%m-%d").date()
        dte = (ed - TODAY).days
        if dte < dte_lo or dte > dte_hi: continue
        try: puts = tk.option_chain(e).puts
        except Exception: continue
        T = dte / 365.0
        for _, row in puts.iterrows():
            bid, ask = float(row.get("bid") or 0), float(row.get("ask") or 0)
            iv = float(row.get("impliedVolatility") or 0)
            K = float(row["strike"])
            if bid <= 0 or ask <= 0 or ask < bid or not (0.05 < iv < 5): continue
            mid = 0.5 * (bid + ask)
            if mid < MIN_PREM or (ask - bid) > max(0.6 * mid, 0.10) * 2: continue  # spread sanity
            dlt = put_delta(spot, K, iv, T)
            if np.isnan(dlt) or not (-0.25 <= dlt <= -0.04): continue
            cand = dict(expiry=e, dte=dte, strike=K, bid=bid, ask=ask, mid=mid, iv=iv, delta=dlt,
                        mkt_volume=int(row.get("volume") or 0), open_interest=int(row.get("openInterest") or 0))
            if best is None or abs(dlt - DELTA_TGT) < abs(best["delta"] - DELTA_TGT):
                best = cand
    return best

def derisk_mult(book):
    """0.5x after the book's last settled period was negative (sign rule)."""
    f = os.path.join(OUT, f"live_{book}_forward_log.csv")
    if not os.path.exists(f): return 1.0, "no prior record -> 1.0x"
    log = pd.read_csv(f)
    done = log.dropna(subset=["realized_return_mid"]) if "realized_return_mid" in log else log.iloc[0:0]
    if len(done) == 0: return 1.0, "no settled period yet -> 1.0x"
    last = float(done.iloc[-1]["realized_return_mid"])
    return (DERISK_MULT, f"last settled period {last:+.4f} < 0 -> {DERISK_MULT}x") if last < 0 \
           else (1.0, f"last settled period {last:+.4f} >= 0 -> 1.0x")

def dump_candidates(book, df, n_sel):
    """Persist the FULL ranked candidate table (every qualifying name's put), not just the
    selected top-N. Needed to later measure whether top-VRP puts beat the ones we passed on.
    Chain quotes are ephemeral (yfinance won't give them back tomorrow) so we snapshot here."""
    c = df.copy().reset_index(drop=True)
    c.insert(0, "asof", str(TODAY))
    c["vrp_rank"] = np.arange(1, len(c) + 1)          # 1 = highest VRP
    c["selected"] = c["vrp_rank"] <= n_sel
    cols = ["asof","vrp_rank","selected","ticker","expiry","dte","strike","delta","iv","rv21","vrp",
            "bid","ask","mid","spot","mkt_volume","open_interest"]
    c = c[[x for x in cols if x in c.columns]]
    fcsv = os.path.join(OUT, f"live_{book}_{TODAY}_candidates.csv")
    c.to_csv(fcsv, index=False)
    print(f"[{book}] {len(c)} candidates ({int(c['selected'].sum())} selected) -> {fcsv}")

def build_singlename(book, dte_lo, dte_hi):
    rows, meta_n = [], 0
    for t in UNIVERSE:
        try:
            tk = yf.Ticker(t)
            h = tk.history(period="4mo")["Close"]
            if len(h) < RV_WIN + 5: continue
            spot, rv = float(h.iloc[-1]), trailing_rv(h)
            if np.isnan(rv): continue
            p = pick_put(tk, spot, dte_lo, dte_hi)
            if p is None: continue
            meta_n += 1
            rows.append(dict(ticker=t, spot=spot, rv21=rv, vrp=p["iv"] - rv, **p))
        except Exception:
            continue
    if not rows: return None, None
    df = pd.DataFrame(rows).sort_values("vrp", ascending=False)
    n_sel = max(5, int(round(TOP_PCT * len(df))))
    dump_candidates(book, df, n_sel)
    sel = df.head(n_sel).copy()
    mult, why = derisk_mult(book)
    sel["weight"] = round(mult / len(sel), 4)
    meta = dict(asof=str(TODAY), book=book, chain_source="yfinance delayed (LIVE)",
                n_candidates=len(df), n_selected=len(sel), vrp_cutoff=round(float(sel["vrp"].min()), 4),
                size_mult=mult, size_reason=why, delta_target=DELTA_TGT,
                dte_window=[dte_lo, dte_hi], rv_window=RV_WIN)
    return sel, meta

def build_xasset():
    rows = []
    for t in ETF_SLEEVES:
        try:
            tk = yf.Ticker(t)
            h = tk.history(period="4mo")["Close"]
            spot, rv = float(h.iloc[-1]), trailing_rv(h)
            p = pick_put(tk, spot, *DTE_MONTHLY)
            if p is None or np.isnan(rv):
                print(f"  xasset: no tradeable put for {t}"); continue
            rows.append(dict(ticker=t, spot=spot, rv21=rv, vrp=p["iv"] - rv, **p))
        except Exception as e:
            print(f"  xasset: {t} failed ({e})")
    if not rows: return None, None
    df = pd.DataFrame(rows)
    inv = 1.0 / df["rv21"]                       # risk-weighted = inverse trailing vol
    mult, why = derisk_mult("xasset")
    df["weight"] = (mult * inv / inv.sum()).round(4)
    meta = dict(asof=str(TODAY), book="xasset", chain_source="yfinance delayed (LIVE)",
                sleeves=ETF_SLEEVES, n_selected=len(df), size_mult=mult, size_reason=why,
                delta_target=DELTA_TGT, dte_window=list(DTE_MONTHLY), rv_window=RV_WIN,
                weighting="inverse trailing RV21")
    return df, meta

def emit(book, sel, meta):
    tag = f"live_{book}_{TODAY}"
    tick = sel.copy()
    tick.insert(0, "action", "SELL_TO_OPEN"); tick.insert(2, "right", "PUT")
    tick["order_type"], tick["limit_price"] = "LIMIT", tick["mid"].round(2)
    cols = ["action","ticker","right","expiry","strike","order_type","limit_price","weight",
            "bid","ask","delta","iv","rv21","vrp","dte","spot","mkt_volume","open_interest"]
    tick = tick[cols].rename(columns={"bid":"ref_bid","ask":"ref_ask"})
    fcsv = os.path.join(OUT, f"{tag}.csv"); tick.to_csv(fcsv, index=False)
    with open(os.path.join(OUT, f"{tag}_meta.json"), "w") as f: json.dump(meta, f, indent=2)
    logf = os.path.join(OUT, f"live_{book}_forward_log.csv")
    entry = pd.DataFrame([dict(asof=str(TODAY), n_selected=meta["n_selected"],
                               size_mult=meta["size_mult"],
                               tickers=";".join(tick["ticker"]),
                               avg_premium_pct=round(float((tick["limit_price"]/tick["strike"]).mean()*100), 3),
                               realized_return_mid=np.nan, realized_return_bid=np.nan)])
    entry.to_csv(logf, mode="a", header=not os.path.exists(logf), index=False)
    print(f"[{book}] {len(tick)} tickets -> {fcsv}")

def already_ran(book, period_key):
    logf = os.path.join(OUT, f"live_{book}_forward_log.csv")
    if not os.path.exists(logf): return False
    return any(str(a).startswith(period_key) for a in pd.read_csv(logf)["asof"])

def main():
    force = set(a.lstrip("-") for a in sys.argv[1:])          # e.g. --weekly --monthly --xasset
    is_mon = TODAY.weekday() == 0
    mon_key = TODAY.strftime("%Y-%m")
    ran = []
    if "weekly" in force or (not force and is_mon):
        if not already_ran("weekly", str(TODAY)):
            s, m = build_singlename("weekly", *DTE_WEEKLY)
            if s is not None: emit("weekly", s, m); ran.append("weekly")
    if "monthly" in force or (not force and not already_ran("monthly", mon_key)):
        s, m = build_singlename("monthly", *DTE_MONTHLY)
        if s is not None: emit("monthly", s, m); ran.append("monthly")
    if "xasset" in force or (not force and not already_ran("xasset", mon_key)):
        s, m = build_xasset()
        if s is not None: emit("xasset", s, m); ran.append("xasset")
    print("DONE", str(TODAY), "books:", ",".join(ran) if ran else "none due today")

if __name__ == "__main__":
    main()
