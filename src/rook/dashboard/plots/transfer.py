import pandas as pd
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

from .base import PlotView

MILLISECS_PER_DAY = 60 * 60 * 24 * 1000


class TransferPlot(PlotView):
    def data(self):
        pdf = pd.DataFrame()
        pdf["time"] = self.df.datetime
        pdf["size"] = self.df["size"]
        pdf["size"] = pdf["size"].apply(lambda x: x / 1024**3)
        pdf = pdf.groupby(pd.Grouper(key="time", freq="1D")).sum()
        pdf = pdf.sort_values(by=["time"], ascending=False)
        return pdf

    def plot(self):
        plot = figure(
            title="Data transfer per day (in GB)",
            tools="",
            toolbar_location=None,
            x_axis_type="datetime",
            sizing_mode="scale_width",
            height=100,
        )
        plot.vbar(
            x="time",
            top="size",
            source=ColumnDataSource(self.data()),
            width=MILLISECS_PER_DAY * 0.7,
            color="blue",
            alpha=0.6,
        )
        plot.y_range.start = 0
        plot.x_range.range_padding = 0.1
        plot.xgrid.grid_line_color = None
        plot.axis.minor_tick_line_color = None
        plot.outline_line_color = None
        # plot.legend.location = "top_left"
        # plot.legend.orientation = "horizontal"
        return plot
