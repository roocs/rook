from pathlib import Path

import bokeh
import humanize
import pandas as pd
from jinja2 import Environment, PackageLoader, select_autoescape

from .models import daily_concurrency, daily_downloads
from .plots import (
    ActivityPlot,
    ConcurrencyPlot,
    DayPlot,
    DownloadsPlot,
    DurationPlot,
    HourPlot,
    TransferPlot,
)
from .tables import MessageTable, OverviewTable

env = Environment(
    loader=PackageLoader("rook.dashboard"), autoescape=select_autoescape()
)
CHUNK_SIZE = 10_000


class Dashboard:
    """
    See dashboard examples:
    * https://engineertodeveloper.com/big-bay-dam-monitoring-dashboard-part-5-bokeh-plots/
    * https://towardsdatascience.com/https-medium-com-radecicdario-next-level-data-visualization-dashboard-app-with-bokeh-flask-c588c9398f98
    """  # noqa

    def __init__(self, output_dir=None):
        self.df = None
        self.df_downloads = None
        self.output_dir = output_dir or Path().cwd().as_posix()

    def load(self, url, filter=None):
        columns = ["uuid", "time_start", "time_end", "status", "message"]
        usecols = [*columns, "operation", "identifier"] if filter else columns
        retained = []
        with pd.read_csv(
            url,
            usecols=usecols,
            parse_dates=["time_start", "time_end"],
            date_format="mixed",
            chunksize=CHUNK_SIZE,
        ) as chunks:
            for chunk in chunks:
                keep = chunk["status"].isin([4, 5])
                if filter:
                    keep &= (chunk["operation"] == "execute") & (
                        chunk["identifier"] == filter
                    )
                selected = chunk.loc[keep, columns]
                if not selected.empty or not retained:
                    retained.append(selected.copy())
        self.df = pd.concat(retained, ignore_index=True).sort_values("time_start")

    def load_downloads(self, url):
        """Retain daily download totals rather than individual log records."""
        daily = None
        with pd.read_csv(
            url,
            usecols=["datetime", "request_type", "size"],
            parse_dates=["datetime"],
            date_format="mixed",
            chunksize=CHUNK_SIZE,
        ) as chunks:
            for chunk in chunks:
                chunk["datetime"] = pd.to_datetime(chunk["datetime"], format="mixed")
                summary = daily_downloads(chunk)
                daily = (
                    summary
                    if daily is None
                    else pd.concat([daily, summary]).groupby(level=0).sum()
                )
        # Include days with no downloads, as the previous full-frame grouping
        # did. They matter for the overview's minimum and median values.
        if not daily.empty:
            daily = daily.reindex(
                pd.date_range(
                    daily.index.min(), daily.index.max(), freq="D", name="datetime"
                ),
                fill_value=0,
            )
        self.df_downloads = daily.reset_index()

    def write(self):
        out = Path(self.output_dir).joinpath("dashboard.html").as_posix()
        with Path(out).open("w") as f:
            f.write(self.render())
        return out

    def render(self):
        template = env.get_template("dashboard.html")
        running = daily_concurrency(self.df)
        script_p1, plot_1 = ActivityPlot(self.df).components()
        script_p2, plot_2 = ConcurrencyPlot(self.df, running=running).components()
        script_p3, plot_3 = DurationPlot(self.df).components()
        script_p4, plot_4 = DayPlot(self.df).components()
        script_p41, plot_41 = HourPlot(self.df).components()
        script_p5, plot_5 = DownloadsPlot(self.df_downloads).components()
        script_p6, plot_6 = TransferPlot(self.df_downloads).components()
        script_t1, table_1 = OverviewTable(
            self.df, self.df_downloads, running=running
        ).components()
        script_t2, table_2 = MessageTable(self.df).components()
        return template.render(
            bokeh_version=bokeh.__version__,
            time_start=humanize.naturaldate(min(self.df["time_start"])),
            time_end=humanize.naturaldate(max(self.df["time_start"])),
            plot_1=plot_1,
            script_p1=script_p1,
            plot_2=plot_2,
            script_p2=script_p2,
            plot_3=plot_3,
            script_p3=script_p3,
            plot_4=plot_4,
            script_p4=script_p4,
            plot_41=plot_41,
            script_p41=script_p41,
            plot_5=plot_5,
            script_p5=script_p5,
            plot_6=plot_6,
            script_p6=script_p6,
            table_1=table_1,
            script_t1=script_t1,
            table_2=table_2,
            script_t2=script_t2,
        )
