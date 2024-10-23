import os
from pathlib import Path

import bokeh
import humanize
import pandas as pd
from jinja2 import Environment, PackageLoader, select_autoescape

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
        # read csv, parse start/end time
        df = pd.read_csv(url, parse_dates=[4, 5])
        # finished jobs
        df = df[df["status"].isin([4, 5])]
        # filter
        if filter:
            df = df.loc[df["operation"] == "execute"].loc[df["identifier"] == filter]
        # order by time
        df = df.sort_values(by=["time_start"], ascending=True)
        # done
        self.df = df

    def load_downloads(self, url):
        # read csv, parse datetime
        df = pd.read_csv(url, parse_dates=[2])
        # done
        self.df_downloads = df

    def write(self):
        out = Path(self.output_dir).joinpath("dashboard.html").as_posix()
        with Path(out).open("w") as f:
            f.write(self.render())
        return out

    def render(self):
        template = env.get_template("dashboard.html")
        script_p1, plot_1 = ActivityPlot(self.df).components()
        script_p2, plot_2 = ConcurrencyPlot(self.df).components()
        script_p3, plot_3 = DurationPlot(self.df).components()
        script_p4, plot_4 = DayPlot(self.df).components()
        script_p41, plot_41 = HourPlot(self.df).components()
        script_p5, plot_5 = DownloadsPlot(self.df_downloads).components()
        script_p6, plot_6 = TransferPlot(self.df_downloads).components()
        script_t1, table_1 = OverviewTable(self.df, self.df_downloads).components()
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
