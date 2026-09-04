# Option-Chain Archive

A daily research capture of the **full US options surface** — every optionable name, both
rights, every strike, every listed expiry — stored so we can backtest *other* strategies later
without needing the data to still be live. This is **separate from the live trading signal**:
`live_signal.py` (the pre-registered top-100 VRP book) is unchanged and stays matched to the
backtest. Nothing here sends orders.

## Scope (decided 2026-07-27)
- **Universe:** all optionable US symbols (NASDAQ Trader listings, probed for a live chain).
- **Depth:** full chain — puts + calls, all strikes, all listed expiries.
- **Retention:** keep everything, zstd-compressed. No auto-deletion.
- **Storage:** primary = the **Box** mount at `%USERPROFILE%\Box\GBC_data\chain_archive`
  (Box streams to its cloud, so it's the durable copy and keeps the near-full C: drive light).
  Chosen 2026-07-27 because C: had only ~21 GB free and Google Drive for desktop wasn't mounted.
  Override with env `CHAIN_ARCHIVE_ROOT` if the mount moves.

## Components
| File | Role |
|------|------|
| `archive_config.py` | Shared config: storage roots, Drive mirror path, scope, concurrency. |
| `build_optionable_universe.py` | Weekly: pull NASDAQ Trader symbol directories, probe each for a listed option chain, cache the optionable set. Resumable. |
| `chain_archive.py` | Daily: pull full chains for every optionable name, write zstd parquet partitioned by date. Resumable via a per-day `_done_tickers.txt` checkpoint. |
| `../run_chain_archive.bat` | Host runner: installs deps, refreshes universe, runs the archive, mirrors to Drive with robocopy. |
| `../setup_chain_archive_schedule.bat` | One-time: registers the weekday 17:30 Task Scheduler job. |
| `read_chain_archive.py` | Example loader (pandas / DuckDB) for querying the archive. |

## Storage layout
```
%USERPROFILE%\Box\GBC_data\chain_archive\
  _universe\optionable_latest.csv           # current optionable ticker list
  _universe\optionable_YYYY-MM-DD.csv       # dated snapshots
  date=YYYY-MM-DD\part-00001.parquet ...    # that day's chains, sharded (200 names/part)
  date=YYYY-MM-DD\_manifest.json            # counts, size, runtime
  date=YYYY-MM-DD\_done_tickers.txt         # resume checkpoint
```
Partitioning by `date=` means DuckDB/pandas/Spark read it as a Hive-partitioned dataset.

## Columns
`asof, snapshot_ts, ticker, right (P/C), expiry, dte, strike, lastPrice, bid, ask,
volume, openInterest, impliedVolatility, inTheMoney, lastTradeDate, spot`

## Storage & runtime expectations
- Data source is **free yfinance delayed quotes** (same as the live signal). End-of-day OI is
  the last value the vendor publishes; treat quotes as delayed, not tick-accurate.
- All-optionable full-chain is large: order **~100–300 MB/day** compressed, **tens of GB/year**.
  Watch the Drive quota; the archive is designed to keep everything, so budget disk accordingly.
- The daily run can take a while (thousands of names x multiple expiries, throttled to
  `MAX_WORKERS` threads). It's scheduled after the close and is fully resumable, so an
  interrupted run continues where it left off on the next invocation.

## First run
1. `python live_paper\build_optionable_universe.py --force`  (build the optionable list)
2. `python live_paper\chain_archive.py`  (capture today)
3. Set `DRIVE_DIR` in `run_chain_archive.bat` to your local Drive path.
4. `setup_chain_archive_schedule.bat`  (register the daily job)

Tune universe breadth / workers via env vars in `archive_config.py`
(`CHAIN_ARCHIVE_ROOT`, `CHAIN_ARCHIVE_DRIVE`, `CHAIN_ARCHIVE_WORKERS`).
