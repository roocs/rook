import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.transform import jitter

from .base import PlotView

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class PulsePlot(PlotView):
    def data(self):
        pdf = pd.DataFrame()
        pdf["day"] = self.df["time_start"].dt.dayofweek
        pdf["day"] = pdf["day"].apply(lambda x: DAYS[x])
        pdf["time"] = self.df["time_start"].dt.time
        return pdf

    def plot(self):
        plot = figure(
            title="Requests by Time of Day",
            tools="",
            toolbar_location=None,
            sizing_mode="scale_width",
            # plot_width=800,
            plot_height=300,
            y_range=list(reversed(DAYS)),
            x_axis_type="datetime",
        )

        plot.circle(
            x="time",
            y=jitter("day", width=0.6, range=plot.y_range),
            source=ColumnDataSource(self.data()),
            alpha=0.3,
        )

        plot.xaxis.formatter.days = ["%Hh"]
        plot.x_range.range_padding = 0
        plot.ygrid.grid_line_color = None
        return plot
