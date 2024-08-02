import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource

from .base import PlotView

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class DayPlot(PlotView):
    def data(self):
        pdf = pd.DataFrame()
        pdf["day"] = self.df["time_start"].dt.dayofweek
        pdf["day"] = pdf["day"].apply(lambda x: DAYS[x])
        # pdf["time"] = self.df["time_start"].dt.time

        day_counts = pdf["day"].value_counts().sort_index()
        # total_count = day_counts.sum()
        # day_percentages = (day_counts / total_count) * 100
        data_ = dict(days=day_counts.index, counts=day_counts.values)
        return data_

    def plot(self):
        plot = figure(
            title="Requests per weekday",
            tools="",
            toolbar_location=None,
            x_range=DAYS,
            # x_axis_type="datetime",
            # sizing_mode="scale_width",
            plot_height=300,
        )
        plot.vbar(
            x="days",
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
        # plot.legend.location = "top_left"
        # plot.legend.orientation = "horizontal"
        return plot
