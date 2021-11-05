import os
import concurrent.futures
import pandas as pd

from pywps import configuration as config

from owslib.wps import WebProcessingService, SYNC

from .base import Usage


URLS = {
    "local": config.get_config_value("server", "url"),
    "dkrz": "http://rook3.cloud.dkrz.de/wps",
    "ceda": "http://rook-wps1.ceda.ac.uk/wps",
}


def get_usage(site, time):
    wps = WebProcessingService(url=URLS[site])
    resp = wps.execute(identifier="usage", inputs=[("time", time)], mode=SYNC)
    # requests
    df = pd.read_csv(
        resp.processOutputs[0].reference, parse_dates=["time_start", "time_end"]
    )
    df["site"] = site
    df["URL"] = URLS[site]
    # downloads
    df_downloads = pd.read_csv(
        resp.processOutputs[1].reference, parse_dates=["datetime"]
    )
    df_downloads["site"] = site
    df_downloads["URL"] = URLS[site]
    return df, df_downloads


def format_time(time_start=None, time_end=None):
    time_start = time_start or ""
    time_end = time_end or ""
    if time_start or time_end:
        time = f"{time_start}/{time_end}"
    else:
        time = ""
    return time


class Combine(Usage):
    def __init__(self, site=None):
        site = site or "local"
        if site == "all":
            self.sites = ["ceda", "dkrz"]
        else:
            self.sites = [site]

    def collect(self, time_start=None, time_end=None, outdir=None):
        time = format_time(time_start, time_end)
        df_list = []
        df_downloads_list = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            jobs = {executor.submit(get_usage, site, time): site for site in self.sites}
            for future in concurrent.futures.as_completed(jobs):
                site = jobs[future]
                try:
                    df, df_downloads = future.result()
                except Exception:
                    raise Exception(f"usage collection for site={site} failed.")
                else:
                    df_list.append(df)
                    df_downloads_list.append(df_downloads)
        # dump usage
        cdf = pd.concat(df_list, ignore_index=True)
        fusage = os.path.join(outdir, "usage.csv")
        cdf.to_csv(fusage, index=False)
        # dump downloads
        cdf = pd.concat(df_downloads_list, ignore_index=True)
        fdownloads = os.path.join(outdir, "downloads.csv")
        cdf.to_csv(fdownloads, index=False)
        return fusage, fdownloads
