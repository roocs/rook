import concurrent.futures
import gzip
import shutil
import time as time_
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen

import pandas as pd
from owslib.wps import ASYNC, WebProcessingService
from pywps import configuration as config

from .base import Usage

URLS = {
    "local": config.get_config_value("server", "url"),
    "ipsl": "http://copernicus-wps.ipsl.fr/wps",
    "dkrz": "http://rook8.cloud.dkrz.de/wps",
}
CHUNK_SIZE = 10_000


def get_usage(site, time, outdir):
    wps = WebProcessingService(url=URLS[site])
    resp = wps.execute(
        identifier="usage",
        inputs=[("time", time)],
        mode=ASYNC,
        output=[("wpsusage", True), ("downloads", True)],
    )
    while resp.isComplete() is False:
        time_.sleep(10)
        resp.checkStatus()

    if not resp.isSucceded():
        raise Exception("usage collection failed.")

    # pandas buffers HTTP responses before parsing, even with chunksize.
    # Download to temporary files first, keeping only bounded buffers in RAM.
    outputs = {output.identifier: output.reference for output in resp.processOutputs}
    paths = []
    for identifier in ("wpsusage", "downloads"):
        path = Path(outdir) / f"{site}-{identifier}.csv"
        with urlopen(outputs[identifier], timeout=300) as response:  # noqa: S310
            with path.open("wb") as output:
                if response.headers.get("Content-Encoding") == "gzip":
                    with gzip.GzipFile(fileobj=response) as uncompressed:
                        shutil.copyfileobj(uncompressed, output, length=1024 * 1024)
                else:
                    shutil.copyfileobj(response, output, length=1024 * 1024)
        paths.append(path)
    return tuple(paths)


def combine_csv(sources, destination):
    """Append site CSVs in bounded chunks, preserving the union of columns."""
    columns = []
    for _, path in sources:
        for column in [*pd.read_csv(path, nrows=0).columns, "site", "URL"]:
            if column not in columns:
                columns.append(column)

    header = True
    with Path(destination).open("w", newline="") as output:
        for site, path in sources:
            with pd.read_csv(
                path, chunksize=CHUNK_SIZE, dtype=str, keep_default_na=False
            ) as chunks:
                for chunk in chunks:
                    chunk["site"] = site
                    chunk["URL"] = URLS[site]
                    chunk.reindex(columns=columns).to_csv(
                        output, index=False, header=header
                    )
                    header = False


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

    def collect(self, time_start=None, time_end=None, outdir=None):
        time = format_time(time_start, time_end)
        fusage = Path(outdir).joinpath("usage.csv").as_posix()
        fdownloads = Path(outdir).joinpath("downloads.csv").as_posix()
        with TemporaryDirectory(dir=outdir, prefix="usage-") as staging:
            usage_sources = []
            download_sources = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                jobs = {
                    executor.submit(get_usage, site, time, staging): site
                    for site in self.sites
                }
                for future in concurrent.futures.as_completed(jobs):
                    site = jobs[future]
                    try:
                        usage, downloads = future.result()
                    except Exception as exc:
                        raise Exception(
                            f"usage collection for site={site} failed."
                        ) from exc
                    usage_sources.append((site, usage))
                    download_sources.append((site, downloads))
            combine_csv(usage_sources, fusage)
            combine_csv(download_sources, fdownloads)
        return fusage, fdownloads
