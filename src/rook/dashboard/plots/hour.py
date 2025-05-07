import pandas as pd
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

from .base import PlotView


class HourPlot(PlotView):
    def data(self):
        # Extract the hour from the datetime column
        pdf = pd.DataFrame({"hour": self.df["time_start"].dt.hour})

        # Count occurrences of each hour and sort by hour
        hour_counts = pdf["hour"].value_counts().sort_index()

        # Create a complete range of hours from 0 to 23, filling missing hours with 0 counts
        all_hours = pd.Series(0, index=range(24))
        all_hours.update(hour_counts)

        # Prepare the data dictionary for Bokeh
        data_ = dict(hours=all_hours.index, counts=all_hours.values)
        return data_

    def plot(self):
        plot = figure(
            title="Requests per Hour of Day",
            sizing_mode="scale_width",
            height=100,
            # x_axis_label="Hour of Day",
            # y_axis_label="Request Count",
            # x_range=HOURS,
        )

        plot.vbar(
            x="hours",
            top="counts",
            source=ColumnDataSource(self.data()),
            width=0.9,
            color="blue",
            alpha=0.5,
        )

        # Additional plot configuration
        plot.y_range.start = 0
        plot.xgrid.grid_line_color = None
        plot.axis.minor_tick_line_color = None
        plot.outline_line_color = None

        return plot
