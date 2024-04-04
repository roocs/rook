import os
import concurrent.futures
import pandas as pd

from pywps import configuration as config

from owslib.wps import WebProcessingService

from .base import Usage


URLS = {
    "local": config.get_config_value("server", "url"),
    "ipsl": "http://copernicus-wps.ipsl.upmc.fr/wps",
    "dkrz": "http://rook3.cloud.dkrz.de/wps",
}


def get_usage(site, time):
    wps = WebProcessingService(url=URLS[site])
    resp = wps.execute(identifier="usage", inputs=[("time", time)])
    # wait until job is done
    while not resp.isComplete():
        print("waiting...")
        resp.checkStatus()
    # usage
    df = pd.read_csv(
        resp.processOutputs[0].reference, parse_dates=["time_start", "time_end"]
    )
    df["site"] = site
    df["URL"] = URLS[site]
    return df


def get_downloads(site, time):
    wps = WebProcessingService(url=URLS[site])
    resp = wps.execute(identifier="downloads", inputs=[("time", time)])
    # wait until job is done
    while not resp.isComplete():
        print("waiting...")
        resp.checkStatus()
    # downloads
    df_downloads = pd.read_csv(
        resp.processOutputs[0].reference, parse_dates=["datetime"]
    )
    df_downloads["site"] = site
    df_downloads["URL"] = URLS[site]
    return df_downloads


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
            self.sites = ["ipsl", "dkrz"]
        else:
            self.sites = [site]

    def collect_usage(self, time_start=None, time_end=None, outdir=None):
        time = format_time(time_start, time_end)
        df_list = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            jobs = {executor.submit(get_usage, site, time): site for site in self.sites}
            for future in concurrent.futures.as_completed(jobs):
                site = jobs[future]
                try:
                    df = future.result()
                except Exception:
                    raise Exception(f"usage collection for site={site} failed.")
                else:
                    df_list.append(df)
        # dump usage
        cdf = pd.concat(df_list, ignore_index=True)
        fusage = os.path.join(outdir, "usage.csv")
        cdf.to_csv(fusage, index=False)
        return fusage

    def collect_downloads(self, time_start=None, time_end=None, outdir=None):
        time = format_time(time_start, time_end)
        df_downloads_list = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            jobs = {executor.submit(get_usage, site, time): site for site in self.sites}
            for future in concurrent.futures.as_completed(jobs):
                site = jobs[future]
                try:
                    df_downloads = future.result()
                except Exception:
                    raise Exception(f"usage collection for site={site} failed.")
                else:
                    df_downloads_list.append(df_downloads)
        # dump downloads
        cdf = pd.concat(df_downloads_list, ignore_index=True)
        fdownloads = os.path.join(outdir, "downloads.csv")
        cdf.to_csv(fdownloads, index=False)
        return fdownloads
