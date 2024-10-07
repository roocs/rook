import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource

from .base import PlotView

MILLISECS_PER_DAY = 60 * 60 * 24 * 1000


class ActivityPlot(PlotView):
    def data(self):
        edf = pd.DataFrame()
        edf["time"] = self.df.time_start
        edf["success"] = self.df.status.apply(lambda x: 0 if x == 5 else 1)
        edf["failed"] = self.df.status.apply(lambda x: 1 if x == 5 else 0)
        gdf = edf.groupby(pd.Grouper(key="time", freq="1D"))
        pdf = gdf.agg(success=("success", "sum"), failed=("failed", "sum"))
        pdf = pdf.sort_values(by=["time"], ascending=False)
        return pdf

    def plot(self):
        plot = figure(
            title="Activity - Requests per day (failures in red)",
            tools="",
            toolbar_location=None,
            x_axis_type="datetime",
            sizing_mode="scale_width",
            height=100,
        )
        status = ["success", "failed"]
        colors = ["green", "red"]
        plot.vbar_stack(
            status,
            x="time",
            source=ColumnDataSource(self.data()),
            width=MILLISECS_PER_DAY * 0.7,
            color=colors,
            alpha=0.6,
            # legend_label=status
        )
        plot.y_range.start = 0
        plot.x_range.range_padding = 0.1
        plot.xgrid.grid_line_color = None
        plot.axis.minor_tick_line_color = None
        plot.outline_line_color = None
        # plot.legend.location = "top_left"
        # plot.legend.orientation = "horizontal"
        return plot
