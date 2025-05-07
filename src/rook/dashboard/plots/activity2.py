import pandas as pd
from bokeh.embed import components
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


def data(df):
    gdf = df.groupby(pd.Grouper(key="time_start", freq="1D")).count()
    pdf = pd.DataFrame()
    pdf["Date"] = pd.to_datetime(gdf.index)
    pdf["Jobs"] = gdf.uuid.values
    return pdf


def plot(df):
    plot = figure(
        title="Activity - Requests per day",
        tools="",
        toolbar_location=None,
        # x_axis_label="Date",
        x_axis_type="datetime",
        # y_axis_label="Requests per day",
        sizing_mode="scale_width",
        height=100,
    )
    plot.line(x="Date", y="Jobs", source=ColumnDataSource(data(df)), color="green")
    return components(plot)
