import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource

from .base import PlotView
from ..models import concurrent_requests


MILLISECS_PER_DAY = 60 * 60 * 24 * 1000


class ConcurrencyPlot(PlotView):
    def data(self):
        cdf = concurrent_requests(self.df)
        # max concurrent per day
        gdf = cdf.groupby(pd.Grouper(key="time", freq="1D")).max()
        pdf = pd.DataFrame()
        pdf["time"] = gdf.index.values
        pdf["running"] = gdf.running.values
        return pdf

    def plot(self):
        plot = figure(
            title="Max concurrent requests per day",
            tools="",
            toolbar_location=None,
            # x_axis_label="Day",
            x_axis_type="datetime",
            # y_axis_label="Jobs in parallel",
            sizing_mode="scale_width",
            plot_height=100,
        )
        plot.vbar(
            x="time",
            top="running",
            source=ColumnDataSource(self.data()),
            width=MILLISECS_PER_DAY * 0.7,
            color="orange",
        )
        plot.y_range.start = 0
        plot.axis.minor_tick_line_color = None
        return plot
