import numpy as np
import pandas as pd
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

from .base import PlotView

MAX_DURATION = 60


class DurationPlot(PlotView):
    def data(self):
        pdf = pd.DataFrame()
        pdf["duration"] = self.df["time_end"] - self.df["time_start"]
        pdf.duration = pdf.duration.dt.seconds
        pdf.duration = pdf.duration.apply(
            lambda x: MAX_DURATION if x > MAX_DURATION else x
        )
        return pdf

    def plot(self):
        hist, edges = np.histogram(self.data().duration, density=True, bins=60)

        plot = figure(
            title="Duration in seconds",
            tools="",
            toolbar_location=None,
            sizing_mode="scale_width",
            plot_height=100,
        )
        plot.quad(
            top=hist,
            bottom=0,
            left=edges[:-1],
            right=edges[1:],
            fill_color="navy",
            line_color="white",
            alpha=0.5,
        )
        plot.y_range.start = 0
        plot.axis.minor_tick_line_color = None
        return plot
