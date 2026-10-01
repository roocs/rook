import pandas as pd


def daily_downloads(df):
    """Return daily counts and bytes from raw downloads or a daily summary."""
    if "download_count" in df.columns:
        return df.set_index("datetime")[["download_count", "size"]]
    if not df["datetime"].notna().any():
        return pd.DataFrame(
            {
                "download_count": pd.Series(dtype="int64"),
                "size": pd.Series(dtype="float64"),
            },
            index=pd.DatetimeIndex([], name="datetime"),
        )
    return df.groupby(pd.Grouper(key="datetime", freq="1D")).agg(
        download_count=("request_type", "count"), size=("size", "sum")
    )


def daily_concurrency(df):
    """Return the existing concurrency metric once per day."""
    return (
        concurrent_requests(df).groupby(pd.Grouper(key="time", freq="1D")).running.max()
    )


def concurrent_requests(df):
    # concurrent requests
    # https://stackoverflow.com/questions/57804145/combining-rows-with-overlapping-time-periods-in-a-pandas-dataframe
    start_df = pd.DataFrame({"time": df["time_start"], "what": 1})
    end_df = pd.DataFrame({"time": df["time_end"], "what": -1})
    merge_df = pd.concat([start_df, end_df]).sort_values("time")
    merge_df["running"] = merge_df["what"].cumsum()
    merge_df = merge_df.loc[merge_df["running"] > 0]
    return merge_df
