# read_chain_archive.py — example loaders for the option-chain archive.
# The archive is Hive-partitioned parquet (date=YYYY-MM-DD/part-*.parquet), so you can query
# it lazily without loading everything. Two idioms shown: pandas (one day) and DuckDB (range).
import os, sys, glob
import archive_config as C


def load_day(date_str):
    """Return a pandas DataFrame of all chains captured on a given date."""
    import pandas as pd
    parts = glob.glob(os.path.join(C.DATA_DIR, f"date={date_str}", "part-*.parquet"))
    if not parts:
        raise FileNotFoundError(f"no archive for {date_str} under {C.DATA_DIR}")
    return pd.concat((pd.read_parquet(p) for p in parts), ignore_index=True)


def query_duckdb(sql):
    """Run SQL over the whole archive. `chains` is the full partitioned dataset.
    Example:
        query_duckdb("SELECT asof, count(*) FROM chains WHERE right='P' GROUP BY 1 ORDER BY 1")
    """
    import duckdb
    glob_path = os.path.join(C.DATA_DIR, "date=*", "part-*.parquet").replace("\\", "/")
    con = duckdb.connect()
    con.execute(f"CREATE VIEW chains AS SELECT * FROM read_parquet('{glob_path}', hive_partitioning=1)")
    return con.execute(sql).df()


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else None
    if d:
        df = load_day(d)
        print(f"{d}: {len(df):,} rows, {df['ticker'].nunique():,} names")
        print(df.head())
    else:
        print("usage: python read_chain_archive.py YYYY-MM-DD")
