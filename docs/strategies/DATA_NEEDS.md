# Data Needs — What's Blocked and on What

*Sean Qin · GBC Downside-Risk Project · 2026-07-04. Status ledger for the P-vs-Q study; updated as pulls land.*

## Blocked on WRDS (arrives ~2026-07-08)

**OptionMetrics IvyDB (highest value — unblocks five things at once):**
1. **Real option bid/ask** — every panel result so far is premium-at-mid with no spread on the digital/put-spread legs (only the index variance-swap and futures legs carry cost assumptions: 0.25 vol-pt half-spread and 1.5 ticks/turnover respectively). Single-name option spreads are 5–15% of premium; the +4.1%/mo τ=0.25 timing cell and all single-name premia need spread-adjusted re-runs before belief.
2. **Truly dead names** — Bloomberg has PURGED SIVB, FRC, LEH, CS (and BSC's IV). Vendor-level survivorship: the worst-case cohort is untestable on the terminal. IvyDB retains delisted names' full option history to 1996.
3. **Real wings** — 10Δ/25Δ per-strike quotes replace my quadratic extrapolation below 90% moneyness; settles whether the τ=0.99 negative premium and τ=0.01 estimates are real or fit artifacts.
4. **Put-spread P&L** — executable backtest of the τ=0.25 structure (strike selection, entry/exit at quoted prices, early-assignment realism for American singles).
5. **Ticker integrity** — BBBY price series runs continuously to 2026 in the Bloomberg pull; ticker recycling suspected. CRSP permno mapping fixes identity through delisting/relisting.

**CRSP:** survivorship-free universes for the panel (all names above $X ADV as of each date, not names alive today); delisting returns (the final-month return of dead names — critical for the seller's true worst case).

**TAQ:** intraday realized variance at scale → HAR-RV/Realized GARCH upgrade of the P-side (Bloomberg intraday caps at ~200 days), and better flash-ambush detection (the 5 ambush months are the strategy's residual risk).

## Blocked on Bloomberg entitlement (not licensed on this terminal)
- 25Δ/10Δ IMPVOL fields and BVOL surface indices (empty on every attempt) — partially superseded by WRDS item 3.
- Single-name CDS; iTraxx.

## Wanted, other sources
- **CBOE DataShop** (paid): 1-min SPX option quotes for intramonth exit rules on the variance leg; VIX9D history pre-2011.
- **Deribit** (free API): BTC/ETH DVOL + option chains → crypto P-vs-Q (the IQN's decisive-win domain at hourly frequency; natural extension).
- **ORATS / Polygon** (cheap alternatives to OptionMetrics if WRDS access lapses after the term).
- **Macro event calendar** (free): FOMC/CPI/NFP dummies — event-day conditioning for the gate (ambush months cluster on macro shocks: Aug-2011 downgrade, Aug-2024 BoJ).

## Bloomberg data WRDS does NOT have (pull while terminal is live)

WRDS ≠ superset of Bloomberg. What only the terminal provides:
1. **Recency** — OptionMetrics lags ~6–12 months, CRSP months; the last year of *everything* is Bloomberg-only. Keep the refresh .bats runnable.
2. **Bloomberg-computed constant-maturity IV surfaces** (the %MNY_DF fields) — OptionMetrics has raw chains and its own delta-surface; same information, different (and lagged) object. Our whole current pipeline keys off the BBG fields.
3. **Futures**: UX1–UX8 VIX curve with volume/OI — WRDS has no futures data. (CME/ICE futures generally absent from standard WRDS.)
4. **Vol indices with history**: MOVE (rates IV), SRVIX, VVIX, SKEW, RVX, OVX, GVZ, VXEEM — not in WRDS (some free from CBOE, MOVE is not).
5. **Credit/funding**: CDX/iTraxx runs, OAS index levels, SOFR-OIS/FRA-OIS, cross-currency basis, GC repo — WRDS lacks (Markit CDS is a separate add-on we likely don't have).
6. **International/ADR IV surfaces** and FX vol — OptionMetrics is US-listed only.
→ Actioned 2026-07-04 night: `pull_tenors.py` (60D/3M smiles for all ~85 single names, 6M + weekly attempts on SPX/SPY/QQQ/IWM) running; UX/vol-index/credit/funding already archived through 07-02 and refreshable via existing bats.

## Already in hand (no dependency)
Bloomberg archive `GBC_data/data/raw/`: SPX + 8 ETF 5-pt smiles (2005+/2012+), 19 adversarial single-name smiles, ~52-ticker broad panel (pulling now), UX1–8 2004+, vol-index family 2004+, FF daily 1926+, VIX 1990+ (free mirror, BBG-verified). All monthly-grid results reproducible from these.

## Explicitly untestable until WRDS
- Seller's P&L through an actual bankruptcy month with real quotes (BBBY/SIVB class).
- IPO year-1 premium (GARCH needs 400+ obs; also motivates the transfer-IQN as the only viable P-side for new listings).
- Spread-adjusted single-name timing (currently: timing signal is DEAD on single names even before costs — t=0.01 — so costs only deepen that conclusion).
