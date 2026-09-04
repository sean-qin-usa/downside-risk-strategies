# IvyDB 1996+ re-pull for the crash-premium asset-pricing paper.
# Spec: PULL_SPEC_IVY96.md. Conventions match wrds_pull_run2.py (pgpass, resumable, gzip).
import builtins, os, sys, calendar, datetime as dt

def _fake_input(prompt=''):
    s = str(prompt).lower()
    if 'username' in s: return 'seanqin2028'
    return 'n'
builtins.input = _fake_input
os.environ['PGPASSFILE'] = r'C:\Users\OWNER\AppData\Roaming\postgresql\pgpass.conf'
os.environ.setdefault('PGUSER', 'seanqin2028')

import pandas as pd
import wrds

OUT = r"C:\GBC_data\data\wrds\ivy96"
os.makedirs(OUT, exist_ok=True)
Y0, Y1 = 1996, 2026  # opprcd years pulled: 1996..2025 (2026 partial if present)

print("connecting...", flush=True)
db = wrds.Connection(wrds_username='seanqin2028')
print("CONNECTED OK", flush=True)

def save(df, name):
    p = os.path.join(OUT, name)
    df.to_csv(p, index=False, compression='gzip' if name.endswith('.gz') else None)
    print('saved', name, len(df), flush=True)

def done(name):
    return os.path.exists(os.path.join(OUT, name))

# ---------- A. Universe: securd + secid-permno link + CRSP common filter ----------
if not done('securd.csv.gz'):
    save(db.raw_sql("select secid, cusip, ticker, issuer, exchange_d from optionm.securd"),
         'securd.csv.gz')
if not done('oclink.csv.gz'):
    save(db.raw_sql("""select secid, permno, sdate, edate, score
                       from wrdsapps.opcrsphist where score <= 2"""),
         'oclink.csv.gz')
if not done('dsenames.csv.gz'):
    save(db.raw_sql("""select permno, namedt, nameendt, shrcd, exchcd, ticker, comnam
                       from crsp.dsenames
                       where shrcd in (10,11) and exchcd in (1,2,3)"""),
         'dsenames.csv.gz')

# ---------- Formation dates: first trading day after 3rd Friday, from CRSP calendar ----------
cal = db.raw_sql(f"select date from crsp.dsi where date >= '{Y0}-01-01' order by date")
cal['date'] = pd.to_datetime(cal['date'])
tdays = cal['date']

def third_friday(y, m):
    c = calendar.monthcalendar(y, m)
    fridays = [w[calendar.FRIDAY] for w in c if w[calendar.FRIDAY]]
    return dt.date(y, m, fridays[2])

form_dates = []
for y in range(Y0, Y1 + 1):
    for m in range(1, 13):
        tf = pd.Timestamp(third_friday(y, m))
        nxt = tdays[tdays > tf]
        if len(nxt): form_dates.append(nxt.iloc[0].date())
form_dates = sorted(set(form_dates))
pd.DataFrame({'form_date': form_dates}).to_csv(os.path.join(OUT, 'formation_dates.csv'), index=False)
print('formation dates:', len(form_dates), flush=True)

# ---------- B. opprcd formation-date snapshots ----------
for yr in range(Y0, Y1):
    f = f'snap_{yr}.csv.gz'
    if done(f):
        print(yr, 'skip', flush=True); continue
    dts = [d for d in form_dates if d.year == yr]
    if not dts: continue
    dl = ",".join(f"'{d}'" for d in dts)
    q = f"""select o.secid, o.optionid, o.date, o.exdate, o.cp_flag, o.strike_price,
                   o.best_bid, o.best_offer, o.impl_volatility, o.delta, o.gamma, o.vega,
                   o.volume, o.open_interest, o.ss_flag
            from optionm.opprcd{yr} o
            where o.date in ({dl})
              and o.exdate - o.date between 15 and 50
              and ((o.cp_flag = 'P' and o.delta between -0.98 and -0.02)
                or (o.cp_flag = 'C' and o.delta between  0.02 and  0.98))
              and o.best_bid >= 0"""
    try:
        d = db.raw_sql(q); save(d, f)
    except Exception as e:
        print('snap', yr, 'ERR', str(e)[:200], flush=True)

# ---------- C. Vol surface (Q-side), both flags ----------
for yr in range(Y0, Y1):
    f = f'surf_{yr}.csv.gz'
    if done(f):
        print('surf', yr, 'skip', flush=True); continue
    try:
        d = db.raw_sql(f"""select secid, date, days, delta, cp_flag, impl_volatility
                           from optionm.stdopd{yr}
                           where days in (10,30,60,91)""")
        save(d, f)
    except Exception as e:
        print('surf', yr, 'ERR', str(e)[:200], flush=True)

# ---------- D. CRSP daily returns + delistings (universe = linked permnos) ----------
link = pd.read_csv(os.path.join(OUT, 'oclink.csv.gz'))
permnos = sorted(set(int(p) for p in link.permno.dropna().unique()))
print('universe permnos:', len(permnos), flush=True)
CH = 500
for yr in range(Y0, Y1 + 1):
    f = f'dsf_{yr}.csv.gz'
    if done(f):
        print('dsf', yr, 'skip', flush=True); continue
    try:
        parts = []
        for i in range(0, len(permnos), CH):
            pl = ",".join(map(str, permnos[i:i + CH]))
            parts.append(db.raw_sql(
                f"""select permno, date, prc, ret, retx, shrout, vol
                    from crsp.dsf
                    where permno in ({pl})
                      and date between '{yr}-01-01' and '{yr}-12-31'"""))
        save(pd.concat(parts, ignore_index=True), f)
    except Exception as e:
        print('dsf', yr, 'ERR', str(e)[:200], flush=True)
if not done('delist.csv.gz'):
    save(db.raw_sql(f"""select permno, dlstdt, dlstcd, dlret, dlretx
                        from crsp.dsedelist where dlstdt >= '{Y0}-01-01'"""),
         'delist.csv.gz')

# ---------- E/F. Zero curve + distributions ----------
if not done('zerocd.csv.gz'):
    save(db.raw_sql(f"select date, days, rate from optionm.zerocd where date >= '{Y0}-01-01'"),
         'zerocd.csv.gz')
if not done('distrd.csv.gz'):
    save(db.raw_sql(f"""select secid, ex_date, amount, distr_type, payment_date
                        from optionm.distrd where ex_date >= '{Y0}-01-01'"""),
         'distrd.csv.gz')

# ---------- G. Earnings dates (Compustat rdq via CCM link) ----------
if not done('rdq.csv.gz'):
    save(db.raw_sql(f"""select l.lpermno as permno, f.gvkey, f.datadate, f.rdq
                        from comp.fundq f
                        join crsp.ccmxpf_lnkhist l on f.gvkey = l.gvkey
                          and l.linktype in ('LU','LC') and l.linkprim in ('P','C')
                          and f.datadate between l.linkdt and coalesce(l.linkenddt,'2099-12-31')
                        where f.rdq is not null and f.datadate >= '{Y0}-01-01'
                          and f.indfmt='INDL' and f.datafmt='STD'
                          and f.popsrc='D' and f.consol='C'"""),
         'rdq.csv.gz')

db.close()
print('IVY96 PULL DONE', flush=True)
