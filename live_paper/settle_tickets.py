# settle_tickets.py — settle expired live paper tickets and fill realized returns.
# Return per ticket (cash-secured): (premium - max(0, K - S_T)) / K, at mid fill and bid fill.
# Book period return = weight-sum of ticket returns; written back into live_{book}_forward_log.csv.
import os, glob, json, datetime as dt
import pandas as pd, numpy as np
import yfinance as yf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "forward_signals")
TODAY = dt.date.today()

def close_on(ticker, day):
    """Official close on `day` (or last close before, for holidays)."""
    d0 = (dt.datetime.strptime(day, "%Y-%m-%d") - dt.timedelta(days=7)).strftime("%Y-%m-%d")
    d1 = (dt.datetime.strptime(day, "%Y-%m-%d") + dt.timedelta(days=1)).strftime("%Y-%m-%d")
    h = yf.Ticker(ticker).history(start=d0, end=d1)["Close"]
    return float(h.iloc[-1]) if len(h) else np.nan

def snapshot_open_tickets():
    """Daily quote snapshot for every open (unexpired) ticket -> our own option-price history.
    Enables fill inference (did the bid ever reach our limit?) and execution tactics research."""
    snapf = os.path.join(ROOT, "live_paper", "quote_snapshots.csv")
    rows = []
    for fcsv in glob.glob(os.path.join(OUT, "live_*_20*.csv")):
        df = pd.read_csv(fcsv)
        book = os.path.basename(fcsv).split("_")[1]
        for _, r in df.iterrows():
            exp = dt.datetime.strptime(str(r["expiry"]), "%Y-%m-%d").date()
            if exp <= TODAY: continue
            try:
                puts = yf.Ticker(r["ticker"]).option_chain(str(r["expiry"])).puts
                q = puts[puts["strike"] == float(r["strike"])]
                if len(q) == 0: continue
                q = q.iloc[0]
                rows.append(dict(snap_date=str(TODAY), book=book, ticker=r["ticker"],
                                 expiry=r["expiry"], strike=r["strike"],
                                 limit_price=r["limit_price"],
                                 bid=float(q.get("bid") or 0), ask=float(q.get("ask") or 0),
                                 last=float(q.get("lastPrice") or 0),
                                 mkt_volume=int(q.get("volume") or 0),
                                 open_interest=int(q.get("openInterest") or 0),
                                 fillable_now=bool(float(q.get("bid") or 0) >= float(r["limit_price"]))))
            except Exception:
                continue
    if rows:
        pd.DataFrame(rows).to_csv(snapf, mode="a", header=not os.path.exists(snapf), index=False)
        nf = sum(r["fillable_now"] for r in rows)
        print(f"snapshot: {len(rows)} open tickets, {nf} currently fillable at limit")

def fill_verified(r):
    """True if any daily snapshot showed bid >= our limit (conservative fill evidence)."""
    snapf = os.path.join(ROOT, "live_paper", "quote_snapshots.csv")
    if not os.path.exists(snapf): return np.nan
    s = pd.read_csv(snapf)
    m = s[(s["ticker"] == r["ticker"]) & (s["expiry"] == r["expiry"]) &
          (s["strike"] == float(r["strike"]))]
    return bool((m["bid"] >= float(r["limit_price"])).any()) if len(m) else np.nan

def settle_file(fcsv):
    df = pd.read_csv(fcsv)
    if "settled_mid" in df.columns and df["settled_mid"].notna().all():
        return df, False
    changed = False
    for i, r in df.iterrows():
        exp = dt.datetime.strptime(str(r["expiry"]), "%Y-%m-%d").date()
        if exp > TODAY or ("settled_mid" in df.columns and pd.notna(r.get("settled_mid"))):
            continue
        ST = close_on(r["ticker"], str(r["expiry"]))
        if np.isnan(ST): continue
        K = float(r["strike"]); loss = max(0.0, K - ST)
        prem_mid = float(r["limit_price"]); prem_bid = float(r["ref_bid"])
        df.loc[i, "S_T"] = round(ST, 2)
        df.loc[i, "settled_mid"] = round((prem_mid - loss) / K, 5)
        df.loc[i, "settled_bid"] = round((prem_bid - loss) / K, 5)
        df.loc[i, "fill_verified"] = fill_verified(r)   # from daily quote snapshots
        changed = True
    if changed: df.to_csv(fcsv, index=False)
    return df, changed

def main():
    snapshot_open_tickets()
    for book in ["weekly", "monthly", "xasset"]:
        logf = os.path.join(OUT, f"live_{book}_forward_log.csv")
        if not os.path.exists(logf): continue
        log = pd.read_csv(logf); updated = False
        for i, entry in log.iterrows():
            if pd.notna(entry.get("realized_return_mid")): continue
            fcsv = os.path.join(OUT, f"live_{book}_{entry['asof']}.csv")
            if not os.path.exists(fcsv): continue
            df, _ = settle_file(fcsv)
            if "settled_mid" not in df.columns or df["settled_mid"].isna().any():
                continue  # not all legs expired yet
            wsum = (df["weight"] * df["settled_mid"]).sum()
            wsum_b = (df["weight"] * df["settled_bid"]).sum()
            log.loc[i, "realized_return_mid"] = round(float(wsum), 5)
            log.loc[i, "realized_return_bid"] = round(float(wsum_b), 5)
            updated = True
            print(f"[{book}] {entry['asof']} settled: mid {wsum:+.4%} bid {wsum_b:+.4%}")
        if updated: log.to_csv(logf, index=False)
    print("SETTLE DONE", TODAY)

if __name__ == "__main__":
    main()
