import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource

from .base import PlotView

MILLISECS_PER_DAY = 60 * 60 * 24 * 1000


class DownloadsPlot(PlotView):
    def data(self):
        pdf = self.df.groupby(pd.Grouper(key="datetime", freq="1D")).count()
        pdf = pdf.sort_values(by=["datetime"], ascending=False)
        return pdf

    def plot(self):
        plot = figure(
            title="Downloads per day",
            tools="",
            toolbar_location=None,
            x_axis_type="datetime",
            sizing_mode="scale_width",
            plot_height=100,
        )
        plot.vbar(
            x="datetime",
            top="request_type",
            source=ColumnDataSource(self.data()),
            width=MILLISECS_PER_DAY * 0.7,
            color="blue",
            alpha=0.5,
        )
        plot.y_range.start = 0
        plot.x_range.range_padding = 0.1
        plot.xgrid.grid_line_color = None
        plot.axis.minor_tick_line_color = None
        plot.outline_line_color = None
        # plot.legend.location = "top_left"
        # plot.legend.orientation = "horizontal"
        return plot
