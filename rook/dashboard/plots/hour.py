import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource

from .base import PlotView

HOURS = [str(i) for i in range(24)]


class HourPlot(PlotView):
    def data(self):
        pdf = pd.DataFrame()
        pdf["hour"] = self.df["time_start"].dt.hour

        hour_counts = pdf["hour"].value_counts().sort_index()
        data_ = dict(hours=hour_counts.index, counts=hour_counts.values)
        return data_

    def plot(self):
        plot = figure(
            title="Requests per hour of day",
            tools="",
            toolbar_location=None,
            # x_range=HOURS,
            sizing_mode="scale_width",
            plot_height=100,
        )
        plot.vbar(
            x="hours",
            top="counts",
            source=ColumnDataSource(self.data()),
            width=0.9,
            color="blue",
            alpha=0.5,
        )
        plot.y_range.start = 0
        # plot.x_range.range_padding = 0.1
        plot.xgrid.grid_line_color = None
        plot.axis.minor_tick_line_color = None
        plot.outline_line_color = None
        return plot
