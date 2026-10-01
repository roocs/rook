import pandas as pd
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

from ..models import daily_concurrency
from .base import PlotView

MILLISECS_PER_DAY = 60 * 60 * 24 * 1000


class ConcurrencyPlot(PlotView):
    def __init__(self, df, running=None):
        super().__init__(df)
        self.running = running

    def data(self):
        running = daily_concurrency(self.df) if self.running is None else self.running
        pdf = pd.DataFrame()
        pdf["time"] = running.index.values
        pdf["running"] = running.values
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
            height=100,
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
