import os
import pandas as pd
import humanize

from .plots import (
    plot_duration,
    plot_jobs_per_day,
    plot_jobs_over_week_days,
    plot_jobs_over_day_time,
    plot_concurrent_jobs_per_day,
    plot_errors_per_day,
    table_of_errors,
)

from jinja2 import Environment, PackageLoader, select_autoescape

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
        self.output_dir = output_dir or os.path.curdir

    def load(self, url, filter=None):
        # read csv, parse start/end time
        df = pd.read_csv(url, parse_dates=[4, 5])
        # day of week
        df["dayofweek"] = df["time_start"].dt.dayofweek
        # hour
        df["hour"] = df["time_start"].dt.hour
        # finished jobs
        df = df[df["status"].isin([4, 5])]
        # filter
        if filter:
            df = df.loc[df["operation"] == "execute"].loc[df["identifier"] == filter]
        # done
        self.df = df

    def write(self):
        out = os.path.join(self.output_dir, "dashboard.html")
        with open(out, "w") as f:
            f.write(self.render())
        return out

    def render(self):
        template = env.get_template("dashboard.html")
        script_1, plot_1 = plot_jobs_per_day(self.df)
        script_2, plot_2 = plot_jobs_over_week_days(self.df)
        script_3, plot_3 = plot_jobs_over_day_time(self.df)
        script_4, plot_4 = plot_concurrent_jobs_per_day(self.df)
        script_41, plot_41 = plot_duration(self.df)
        script_5, plot_5 = plot_errors_per_day(self.df)
        script_errors, table_errors = table_of_errors(self.df)
        return template.render(
            time_start=humanize.naturaldate(self.df["time_start"].dt.date.values[0]),
            time_end=humanize.naturaldate(self.df["time_end"].dt.date.values[-1]),
            plot_1=plot_1,
            script_1=script_1,
            plot_2=plot_2,
            script_2=script_2,
            plot_3=plot_3,
            script_3=script_3,
            plot_4=plot_4,
            script_4=script_4,
            plot_41=plot_41,
            script_41=script_41,
            plot_5=plot_5,
            script_5=script_5,
            table_errors=table_errors,
            script_errors=script_errors,
        )
