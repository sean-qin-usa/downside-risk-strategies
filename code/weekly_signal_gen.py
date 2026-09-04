# -*- coding: utf-8 -*-
"""
WEEKLY cross-sectional VRP short-put SIGNAL generator (P-vs-Q strategy).
Runs on the HOST (has C:\\GBC_data + WRDS auth). Produces a broker-ready blotter of
SELL_TO_OPEN put tickets. NEVER sends orders -- a human reviews and submits.

Spec (weekly arm, validated strategy_research_state.md 8a / netcost_weekly_vs_monthly.json):
  universe : top-100 single-name underlyings by option open interest (spreads_2023.csv.gz)
  signal   : SELL puts on top-10% names by VRP = IV(delta ~= -0.12 put) - trailing 21d realized vol
  tenor    : 5-15 DTE weekly puts, held to expiry, cash-secured
  limit    : mid = (best_bid + best_offer)/2
  sizing   : 0.5x if the strategy's own prior recorded week was negative, else 1.0x

WRDS auth reused from wrds_pull_calls_light.py (saved pgpass). Password is NEVER read/typed/handled.
"""
import builtins, os, sys, math, json, glob, datetime as dt

# --- WRDS auth: same non-interactive pattern as wrds_pull_calls_light.py (uses saved pgpass) ---
def _fake_input(p=''):
    s = str(p).lower()
    return 'seanqin2028' if 'username' in s else 'n'
builtins.input = _fake_input
os.environ['PGPASSFILE'] = r'C:\Users\OWNER\AppData\Roaming\postgresql\pgpass.conf'
os.environ.setdefault('PGUSER', 'seanqin2028')

import numpy as np, pandas as pd

P   = r"C:\Users\OWNER\Claude\Projects\GBC Project"
W   = r"C:\GBC_data\data\wrds"
RAW = r"C:\GBC_data\data\raw"
FS  = os.path.join(P, "forward_signals")
os.makedirs(FS, exist_ok=True)

TODAY = dt.date.today()
LOGP  = os.path.join(P, "weekly_signal_run.log")
LOG   = open(LOGP, "w", encoding="utf-8")
def lg(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True); LOG.write(m + "\n"); LOG.flush()

lg("=== WEEKLY VRP SHORT-PUT SIGNAL ===", TODAY.isoformat())

# ---- config ----
DELTA_TARGET = -0.12
DTE_LO, DTE_HI = 5, 15
RV_WIN = 21
TOPPCT = 0.10
DERISK = 0.5
NUNI   = 100

# this-Friday reference (task wording); actual expiry is driven by the selected 5-15 DTE contract
dow = TODAY.weekday()                       # Mon=0
this_friday = TODAY + dt.timedelta(days=(4 - dow) % 7)
lg("this_friday(ref) =", this_friday, "| note: 5-15 DTE window may land on the following Friday")

# ---- secid -> ticker ----
sym = {int(r.secid): str(r.ticker)
       for r in pd.read_csv(os.path.join(W, "secids.csv"))
                   .dropna(subset=['secid']).astype({'secid': int}).itertuples()}
lg("secids mapped:", len(sym))

# ---- rank top-100 by open interest ----
oi = (pd.read_csv(os.path.join(W, "spreads_2023.csv.gz"), usecols=['secid', 'open_interest'])
        .groupby('secid')['open_interest'].sum().sort_values(ascending=False))
ranked = [int(s) for s in oi.index]
top = ranked[:NUNI]
secl = ",".join(str(s) for s in top)
lg("top-100 secids by OI ready; head:", top[:8])

# ---- get most recent weekly put chain (live WRDS first, then local fallback) ----
chain = None; snapdate = None; source = None
try:
    import wrds
    lg("connecting WRDS (saved pgpass; no password handled)...")
    db = wrds.Connection(wrds_username='seanqin2028')
    lg("CONNECTED")
    for yr in (2026, 2025, 2024):
        try:
            mx = db.raw_sql(f"select max(date) d from optionm.opprcd{yr} where secid in ({secl})")
            d = mx['d'].iloc[0]
            if d is None:
                lg("year", yr, "-> no rows for universe"); continue
            snapdate = pd.to_datetime(d).date()
            lg("year", yr, "most recent available date:", snapdate)
            q = f"""select o.secid,o.date,o.exdate,o.cp_flag,o.strike_price,o.best_bid,
                    o.best_offer,o.impl_volatility,o.volume,o.open_interest,o.delta
                    from optionm.opprcd{yr} o
                    where o.secid in ({secl}) and o.cp_flag='P' and o.date='{snapdate}'
                      and o.exdate - o.date between {DTE_LO} and {DTE_HI}
                      and o.delta between -0.20 and -0.05"""
            c = db.raw_sql(q)
            lg("year", yr, "weekly put chain rows:", len(c))
            if len(c) > 0:
                chain = c; source = f"WRDS optionm.opprcd{yr} @ {snapdate}"; break
        except Exception as e:
            lg("year", yr, "query ERR:", str(e)[:160])
    db.close()
except Exception as e:
    lg("WRDS live pull unavailable:", str(e)[:200])

# ---- fallback: most recent local weekly snapshot ----
if chain is None or len(chain) == 0:
    lg("live pull empty -> FALLBACK to most recent local chain snapshot")
    cand_files = sorted(glob.glob(os.path.join(W, "*dte05_15*.csv.gz"))) or \
                 sorted(glob.glob(os.path.join(W, "*weekly*.csv.gz")))
    use_files = cand_files[-1:] if cand_files else sorted(glob.glob(os.path.join(W, "spreads_[12]*.csv.gz")))[-1:]
    lg("fallback file(s):", use_files)
    frames = []
    uset = set(top)
    for f in use_files:
        cols = ['secid','date','exdate','cp_flag','strike_price','best_bid','best_offer','impl_volatility','delta']
        for ch in pd.read_csv(f, chunksize=1000000):
            keep = [c for c in cols if c in ch.columns]
            ch = ch[keep]
            ch = ch[ch.secid.isin(uset)]
            frames.append(ch)
    if frames:
        c = pd.concat(frames, ignore_index=True)
        c['date'] = pd.to_datetime(c['date']); c['exdate'] = pd.to_datetime(c['exdate'])
        if 'cp_flag' in c.columns:
            c = c[c.cp_flag == 'P']
        c['dte'] = (c['exdate'] - c['date']).dt.days
        c = c[(c.dte >= DTE_LO) & (c.dte <= DTE_HI) & (c.delta.between(-0.20, -0.05))]
        snapdate = c['date'].max().date()
        c = c[c['date'] == pd.Timestamp(snapdate)]
        chain = c; source = f"LOCAL {os.path.basename(use_files[0])} @ {snapdate}"
        lg("fallback weekly chain rows:", len(chain), "snapdate:", snapdate)

if chain is None or len(chain) == 0:
    lg("FATAL: no weekly chain available from WRDS or local. Aborting."); LOG.close(); sys.exit(2)
lg("CHAIN SOURCE:", source)

chain = chain.copy()
chain['date']   = pd.to_datetime(chain['date'])
chain['exdate'] = pd.to_datetime(chain['exdate'])
chain['dte']    = (chain['exdate'] - chain['date']).dt.days

# ---- trailing 21d realized vol from tpx_{ticker}.csv, as of snapdate ----
def trailing_rv(ticker, asof, window=RV_WIN):
    f = os.path.join(RAW, f"tpx_{ticker}.csv")
    if not os.path.exists(f):
        return np.nan
    t = pd.read_csv(f)
    if 'field' in t.columns:
        t = t[t['field'] == 'PX_LAST'][['date', 'value']].rename(columns={'value': 'px'})
    else:
        pxcol = 'PX_LAST' if 'PX_LAST' in t.columns else t.columns[-1]
        t = t.rename(columns={pxcol: 'px'})[['date', 'px']]
    t['date'] = pd.to_datetime(t['date']); t = t.dropna().sort_values('date')
    t = t[t['date'] <= pd.Timestamp(asof)]
    if len(t) < window + 1:
        return np.nan
    lr = np.log(t['px'] / t['px'].shift(1)).dropna().tail(window)
    return float(lr.std() * math.sqrt(252))

# ---- one put nearest delta=-0.12 per name; VRP = IV - RV ----
cand = []
for s, g in chain.groupby('secid'):
    g = g[(g.best_bid > 0) & (g.best_offer > 0) & g.impl_volatility.notna() & (g.delta < 0)]
    if not len(g):
        continue
    r = g.iloc[(g.delta - DELTA_TARGET).abs().values.argmin()]
    tk = sym.get(int(s), str(int(s)))
    rv = trailing_rv(tk, snapdate)
    if not np.isfinite(rv):
        continue
    iv = float(r.impl_volatility)
    bid, off = float(r.best_bid), float(r.best_offer)
    cand.append(dict(secid=int(s), ticker=tk, right="PUT",
                     expiry=str(pd.to_datetime(r.exdate).date()),
                     dte=int((pd.to_datetime(r.exdate) - pd.to_datetime(r.date)).days),
                     strike=round(float(r.strike_price) / 1000.0, 2),
                     delta=round(float(r.delta), 3), iv=round(iv, 4), rv21=round(rv, 4),
                     vrp=round(iv - rv, 4), ref_bid=bid, ref_ask=off,
                     limit_price=round((bid + off) / 2, 2)))
lg("candidates with VRP:", len(cand))
if not cand:
    lg("FATAL: zero candidates after RV join."); LOG.close(); sys.exit(3)

cdf = pd.DataFrame(cand).sort_values('vrp', ascending=False).reset_index(drop=True)
thr = cdf['vrp'].quantile(1 - TOPPCT)
sel = cdf[cdf['vrp'] >= thr].copy()
lg("VRP cutoff (top-10%):", round(float(thr), 4), "| selected:", len(sel))

# ---- sizing: 0.5x if the strategy's own prior recorded week was negative, else 1.0x ----
logcsv = os.path.join(FS, "weekly_forward_log.csv")
size_mult = 1.0; size_reason = "no prior weekly record -> full size 1.0x (first weekly run)"
if os.path.exists(logcsv):
    try:
        fl = pd.read_csv(logcsv)
        fl = fl[fl.get('asof') != TODAY.isoformat()] if 'asof' in fl.columns else fl
        prior = fl.dropna(subset=['realized_return']) if 'realized_return' in fl.columns else fl.iloc[0:0]
        if len(prior):
            last = prior.sort_values('asof').iloc[-1]
            lastret = float(last['realized_return'])
            if lastret < 0:
                size_mult = DERISK; size_reason = f"prior week {last['asof']} realized {lastret:+.4f} < 0 -> de-risk 0.5x"
            else:
                size_reason = f"prior week {last['asof']} realized {lastret:+.4f} >= 0 -> full 1.0x"
        else:
            size_reason = "prior weeks logged but none have a realized_return yet -> full size 1.0x"
    except Exception as e:
        lg("size-check read warn:", str(e)[:120])
sel['weight'] = round(1.0 / len(sel), 4) * size_mult
lg("SIZE:", size_mult, "|", size_reason)

# ---- blotter ----
blot = sel.assign(action="SELL_TO_OPEN", order_type="LIMIT")[
    ['action','ticker','right','expiry','strike','order_type','limit_price','weight',
     'ref_bid','ref_ask','delta','iv','rv21','vrp','dte']].reset_index(drop=True)
outcsv = os.path.join(FS, f"weekly_signal_{TODAY.isoformat()}.csv")
blot.to_csv(outcsv, index=False)
lg("BLOTTER WRITTEN:", outcsv, "rows:", len(blot))

meta = dict(asof=TODAY.isoformat(), strategy="weekly-VRP-short-put", chain_source=source,
            snapshot_date=str(snapdate), this_friday_ref=str(this_friday),
            n_candidates=int(len(cdf)), n_selected=int(len(sel)),
            vrp_cutoff=round(float(thr), 4), size_mult=size_mult, size_reason=size_reason,
            delta_target=DELTA_TARGET, dte_window=[DTE_LO, DTE_HI], rv_window=RV_WIN)
json.dump(meta, open(os.path.join(FS, f"weekly_signal_{TODAY.isoformat()}_meta.json"), "w"), indent=2, default=str)

# ---- append to running weekly forward log (for next week's size check + track record) ----
row = dict(asof=TODAY.isoformat(), snapshot_date=str(snapdate), n_selected=int(len(sel)),
           size_mult=size_mult, vrp_cutoff=round(float(thr), 4),
           tickers=";".join(sel['ticker'].tolist()),
           avg_limit=round(float(sel['limit_price'].mean()), 3),
           realized_return="")  # to be filled once fills/expiry known
if os.path.exists(logcsv):
    fl = pd.read_csv(logcsv)
    fl = fl[fl['asof'] != TODAY.isoformat()]
    fl = pd.concat([fl, pd.DataFrame([row])], ignore_index=True)
else:
    fl = pd.DataFrame([row])
fl.to_csv(logcsv, index=False)
lg("WEEKLY FORWARD LOG updated:", logcsv, "| total weeks:", len(fl))

# echo blotter to log
lg("---- BLOTTER ----")
for r in blot.itertuples(index=False):
    lg(f"  SELL_TO_OPEN {r.ticker:6s} PUT {r.expiry}  K={r.strike:<8}  LIMIT={r.limit_price:<6} "
       f"w={r.weight:<6} bid/ask={r.ref_bid}/{r.ref_ask}  d={r.delta}  IV={r.iv} RV={r.rv21}  VRP={r.vrp}")
lg("=== DONE_WEEKLY_SIGNAL ===")
LOG.close()
print("DONE_WEEKLY_SIGNAL", flush=True)
