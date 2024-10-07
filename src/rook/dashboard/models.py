import pandas as pd


def concurrent_requests(df):
    # concurrent requests
    # https://stackoverflow.com/questions/57804145/combining-rows-with-overlapping-time-periods-in-a-pandas-dataframe
    start_df = pd.DataFrame({"time": df["time_start"], "what": 1})
    end_df = pd.DataFrame({"time": df["time_end"], "what": -1})
    merge_df = pd.concat([start_df, end_df]).sort_values("time")
    merge_df["running"] = merge_df["what"].cumsum()
    merge_df = merge_df.loc[merge_df["running"] > 0]
    return merge_df
