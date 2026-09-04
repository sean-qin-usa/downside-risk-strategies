# Bloomberg data acquisition plan — what needs Bloomberg, and why

Purpose: a single map of every research path that is blocked on Bloomberg data, the exact securities/fields/history to pull, and the priority order — so a future Bloomberg session can grab everything in one pass. Everything NOT listed here has already been done on non-Bloomberg data (CRSP, M5, simulation).

## How to pull (mechanics)
- The host PC has a Bloomberg Terminal + the `xbbg`/pyo3-xbbg Python bindings (used by the earlier host jobs).
- Daily history: `blp.bdh(tickers, 'PX_LAST', start, end)` (add `PX_VOLUME` where useful). Save each study's panel as CSV to `C:\GBC_data\`, then `scp` to `ai2:~/sean_dev/GBC_data/` so the ai2 GPU pipeline can run the models.
- Intraday/hourly: `blp.bdib(ticker, event='TRADE', interval=60)` per name (rate-limited; pull in batches).
- One Terminal login covers all of the below. Pull once, cache as CSV, reuse.

## The blocked research paths (priority order)

### P1 — Crisis-FX significance (small pull, high payoff)
Turns the biggest single-asset WIN into a *significant* result. We found nonparam beats GARCH-t by 12-14% on hyperinflation FX (USDARS, USDEGP, USDNGN) but only as point estimates — no Diebold-Mariano / MCS yet (per-day losses weren't cached).
- Securities (24 `... Curncy`): EURUSD, USDJPY, GBPUSD, USDCHF, AUDUSD, USDCAD, USDSEK (majors); USDMXN, USDBRL, USDZAR, USDINR, USDIDR, USDTHB, USDKRW, USDPHP, USDCLP, USDPLN (EM); USDTRY, USDARS, USDRUB, USDEGP, USDNGN, USDUAH, USDPKR (crisis).
- Field PX_LAST, daily, longest available history (many back to mid-1990s; ARS/TRY/EGP the key ones).
- Plug-in: re-run `job_fx_study.py` with per-date DM + MCS added (like `misspec_significance.py`), and fix the `over_time` window bug (returned 0 windows) and the `resid_kurt=None` bug.

### P1 — Korea deep case study (re-run with rigor)
The emerging/crisis-market case study; ran once but needs the significance layer + bug fixes.
- Indices: KOSPI, KOSDAQ, KOSPI200, VKOSPI (`... Index`). FX: USDKRW Curncy. Rates: KTB 3Y & 10Y (govt yield tickers). 
- Single names (`... Equity`, KS/KQ): Samsung Elec, SK Hynix, Naver, Kakao, Krafton, EcoPro, EcoProBM, KakaoGames, Hanwha Aero, Korea Aero, Hyundai Rotem, Samsung Bio, Alteogen, HYBE, Hanwha Ocean, HD Hyundai Heavy.
- Field PX_LAST daily, 2010-present (covers the 2026 AI-rally/circuit-breaker window). 
- Plug-in: re-run `job_korea_deep.py` with DM/MCS + the FRTB backtests (Kupiec/Christoffersen); fix `resid_kurt=None` (the misspecification metric that failed to compute) so we can locate Korea on the misspecification frontier.

### P2 — Universal cross-asset FRTB flagship table
The one cross-asset table for the paper, with full FRTB rigor (currently only run as point estimates; and CAViaR/EVT/backtests not applied).
- ~43 instruments already scripted in `job_universal_bench.py`: equity indices (SPX, NDX), single names (AAPL, XOM), FX (majors + crisis), rates (US2Y/US10Y/BUND), credit (IG_OAS, HY_OAS), commodities (COPPER, CORN, CRUDE, NATGAS, GOLD, SILVER, WHEAT, SOYBEAN, COFFEE, SUGAR, COCOA, COTTON, PLATINUM, PALLADIUM, ALUMINUM, NICKEL), power (PJM, ERCOT), vol (VIX, VVIX, V2X, MOVE), crypto (BTC, ETH), shipping (BALTIC_DRY), carbon (CARBON_EU).
- Field PX_LAST daily, longest history each.
- Plug-in: run the `frtb_bench.py` + `frtb_caviar.py` + `frtb_hybrid_evt.py` battery per asset class → one table with DM/MCS + Kupiec/Christoffersen. Shows "industry-standard-and-above" across every asset class, not just US equities.

### P2 — Cross-country stability gradient (developed → frontier)
The "amortization across countries / first-to-third-world" program.
- Equity indices for a stratified set: developed (SPX, SX5E, UKX, NKY, TSX), EM (KOSPI, TWSE, NIFTY, IBOV, MEXBOL, JALSH), frontier (VNINDEX, EGX30, KSE100, NGSEINDX, CASE...). Plus each country's USD FX pair (already in the FX list).
- Field PX_LAST daily, longest history.
- Plug-in: amortized model + misspecification-frontier score per country → does the nonparam edge scale with country "misspecification"/instability? 
- NOTE: much of this can be done WITHOUT Bloomberg via WRDS Compustat Global (international equities/indices) + FRED — a fallback if Bloomberg is delayed.

### P3 — Crypto (finish) + intraday/high-frequency
- Crypto daily: BTC, ETH, XRP, LTC, DOGE done; BCH, SOL errored (re-pull). Field PX_LAST daily.
- Crypto HOURLY: the one place IQN already won (~0.6%); pull `bdib` hourly bars for BTC/ETH to extend.
- Intraday EQUITY: hourly bars for a set of S&P names (tasks #15-17, still pending) — the intraday IQN-vs-GARCH tournament.
- Vol indices as predictands: VKOSPI, VIX, VVIX, MOVE (mean-reverting, heavy-tailed — a good nonparam test).

## Non-Bloomberg fallbacks (can do now if Bloomberg stays unavailable)
- WRDS Compustat Global → international equities/indices (substitute for the cross-country gradient).
- WRDS CRSP → longer US panel (2000-2024, adds the 2008 crisis we currently lack; our panel is 2014-2024).
- FRED → rates, macro, credit spreads. Ken French → factors. GEFCom2014 → electricity (open competition data).

## Summary: one Bloomberg session, in order
1. FX 24 pairs (daily, full history) — crisis-FX significance. [tiny pull, biggest payoff]
2. Korea 23 tickers (daily, 2010+) — case study with rigor.
3. Universal ~43 instruments (daily, full history) — FRTB flagship table.
4. Cross-country indices (~20-30 countries, daily) — stability gradient.
5. Crypto re-pull + hourly; intraday equity bars; vol indices.
Save all as CSV in `C:\GBC_data`, scp to ai2, then the existing model scripts run unchanged.
