from pathlib import Path

import pandas as pd
from pywps import configuration as config

from .base import Usage


class WPSUsage(Usage):
    def collect(self, time_start=None, time_end=None, outdir=None):
        db_conn = config.get_config_value("logging", "database")
        df = pd.read_sql(
            sql="pywps_requests", con=db_conn, parse_dates=["time_start", "time_end"]
        )
        df = df.loc[df["operation"] == "execute"]
        if time_start:
            df = df.loc[df["time_start"] >= time_start]
        if time_end:
            df = df.loc[df["time_end"] <= time_end]
        fname = Path(outdir).joinpath("wps_requests.csv").as_posix()
        df.to_csv(fname, index=False)
        return fname
