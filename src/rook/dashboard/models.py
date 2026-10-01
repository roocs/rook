import numpy as np
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
    """Compute daily peaks without building the full event DataFrame."""
    times = pd.concat([df["time_start"], df["time_end"]], ignore_index=True).array
    # Match sort_values' ordering, including ties and missing timestamps.
    order = times.argsort(kind="quicksort", na_position="last")
    times = times.take(order)
    running = np.empty(len(order), dtype=np.int64)
    # Starts occupied the first half of the unsorted events; ends the second.
    np.less(order, len(df), out=running)
    del order
    running *= 2
    running -= 1
    np.cumsum(running, out=running)
    counts = pd.Series(
        running, index=pd.DatetimeIndex(times, name="time"), name="running"
    )
    # Preserve the existing positive-event-only metric and empty-day handling.
    return counts[counts > 0].groupby(pd.Grouper(freq="1D")).max()


def concurrent_requests(df):
    # concurrent requests
    # https://stackoverflow.com/questions/57804145/combining-rows-with-overlapping-time-periods-in-a-pandas-dataframe
    start_df = pd.DataFrame({"time": df["time_start"], "what": 1})
    end_df = pd.DataFrame({"time": df["time_end"], "what": -1})
    merge_df = pd.concat([start_df, end_df]).sort_values("time")
    merge_df["running"] = merge_df["what"].cumsum()
    merge_df = merge_df.loc[merge_df["running"] > 0]
    return merge_df
