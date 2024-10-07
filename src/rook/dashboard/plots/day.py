import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource

from .base import PlotView

# Constant to represent days of the week
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class DayPlot(PlotView):
    def data(self):
        pdf = pd.DataFrame()

        # Convert the 'time_start' column to day of the week and map it to the DAYS constant
        pdf["day"] = self.df["time_start"].dt.dayofweek
        pdf["day"] = pdf["day"].apply(lambda x: DAYS[x])

        # Create a dictionary with the sorted day names and their corresponding counts
        day_counts = pdf["day"].value_counts().sort_index()
        data_ = dict(days=day_counts.index, counts=day_counts.values)
        return data_

    def plot(self):
        # Create a Bokeh figure for plotting
        plot = figure(
            title="Requests per Weekday",
            tools="",  # No interactive tools
            toolbar_location=None,
            x_range=DAYS,  # Set x-axis range to days of the week
            sizing_mode="scale_width",
            plot_height=100,
        )

        # Create a vertical bar chart
        plot.vbar(
            x="days",
            top="counts",
            source=ColumnDataSource(self.data()),
            width=0.9,
            color="blue",
            alpha=0.5,
        )

        # Set the y-axis to start from 0
        plot.y_range.start = 0
        plot.xgrid.grid_line_color = None  # Remove grid lines on x-axis
        plot.axis.minor_tick_line_color = None  # Remove minor ticks
        plot.outline_line_color = None  # Remove the outline around the plot

        return plot
