import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, TableColumn, DataTable
from bokeh.embed import components

TOOLS = ""  # pan, wheel_zoom, box_zoom, reset, save"


def jobs_per_day(df):
    gdf = df.groupby(pd.Grouper(key="time_start", freq="1D")).count()
    pdf = pd.DataFrame()
    pdf["Date"] = pd.to_datetime(gdf.index)
    pdf["Jobs"] = gdf.uuid.values
    return pdf


def plot_jobs_per_day(df):
    plot = figure(
        title="Jobs per day",
        tools=TOOLS,
        toolbar_location=None,
        x_axis_label="Date",
        x_axis_type="datetime",
        y_axis_label="Jobs per day",
        sizing_mode="scale_width",
        plot_height=450,
    )
    plot.line(x="Date", y="Jobs", source=ColumnDataSource(jobs_per_day(df)))
    return components(plot)


def jobs_over_week_days(df):
    gdf = df.groupby(pd.Grouper(key="dayofweek")).count()
    gdf = gdf.sort_index()
    pdf = pd.DataFrame()
    pdf["Week Day"] = gdf.index.values
    pdf["Jobs"] = gdf.uuid.values
    return pdf


def plot_jobs_over_week_days(df):
    plot = figure(
        title="Jobs over week days",
        tools=TOOLS,
        toolbar_location=None,
        x_axis_label="Week Day",
        # x_axis_type="datetime",
        y_axis_label="Jobs",
        sizing_mode="scale_width",
        plot_height=450,
    )
    plot.vbar(
        x="Week Day", top="Jobs", source=ColumnDataSource(jobs_over_week_days(df))
    )
    return components(plot)


def jobs_over_day_time(df):
    gdf = df.groupby(pd.Grouper(key="hour")).count()
    gdf = gdf.sort_index()
    pdf = pd.DataFrame()
    pdf["Hour"] = gdf.index.values
    pdf["Jobs"] = gdf.uuid.values
    return pdf


def plot_jobs_over_day_time(df):
    plot = figure(
        title="Jobs over day time",
        tools=TOOLS,
        toolbar_location=None,
        x_axis_label="Hour",
        # x_axis_type="datetime",
        y_axis_label="Jobs",
        sizing_mode="scale_width",
        plot_height=450,
    )
    plot.vbar(x="Hour", top="Jobs", source=ColumnDataSource(jobs_over_day_time(df)))
    return components(plot)


def concurrent_jobs(df):
    # https://stackoverflow.com/questions/57804145/combining-rows-with-overlapping-time-periods-in-a-pandas-dataframe
    start_df = pd.DataFrame({"time": df["time_start"], "what": 1})
    end_df = pd.DataFrame({"time": df["time_end"], "what": -1})
    merge_df = pd.concat([start_df, end_df]).sort_values("time")
    merge_df["running"] = merge_df["what"].cumsum()
    merge_df = merge_df.loc[merge_df["running"] > 0]
    return merge_df


def concurrent_jobs_per_day(df):
    new_df = concurrent_jobs(df)
    group_df = new_df.groupby(pd.Grouper(key="time", freq="1D")).max()
    new_df = pd.DataFrame()
    new_df["time"] = group_df.index.values
    new_df["running"] = group_df.running.values
    return new_df


def plot_concurrent_jobs_per_day(df):
    plot = figure(
        title="Max concurrent jobs per day",
        tools=TOOLS,
        toolbar_location=None,
        x_axis_label="Day",
        x_axis_type="datetime",
        y_axis_label="Jobs in parallel",
        sizing_mode="scale_width",
        plot_height=450,
    )
    plot.vbar(
        x="time", top="running", source=ColumnDataSource(concurrent_jobs_per_day(df))
    )
    return components(plot)


def duration(df):
    df["duration"] = df["time_end"] - df["time_start"]
    df.duration = df.duration.dt.seconds / 60 + 1
    gdf = df.groupby(pd.Grouper(key="duration")).count()
    gdf = gdf.sort_index()
    pdf = pd.DataFrame()
    pdf["Duration"] = gdf.index.values
    pdf["Jobs"] = gdf.uuid.values
    return pdf


def plot_duration(df):
    plot = figure(
        title="Job Duration",
        tools=TOOLS,
        toolbar_location=None,
        x_axis_label="Duration (minutes)",
        # x_axis_type="datetime",
        y_axis_label="Jobs",
        sizing_mode="scale_width",
        plot_height=450,
    )
    plot.vbar(x="Duration", top="Jobs", source=ColumnDataSource(duration(df)))
    return components(plot)


def errors_per_day(df):
    new_df = df.loc[df["status"] == 5]
    gdf = new_df.groupby(pd.Grouper(key="time_start", freq="1D")).count()
    pdf = pd.DataFrame()
    pdf["Date"] = pd.to_datetime(gdf.index)
    pdf["Errors"] = gdf.uuid.values
    return pdf


def plot_errors_per_day(df):
    plot = figure(
        title="Errors per day",
        tools=TOOLS,
        toolbar_location=None,
        x_axis_label="Day",
        x_axis_type="datetime",
        y_axis_label="Errors",
        sizing_mode="scale_width",
        plot_height=450,
    )
    plot.vbar(x="Date", top="Errors", source=ColumnDataSource(errors_per_day(df)))
    return components(plot)


def error_messages(df):
    new_df = df.loc[df["status"] == 5]
    gdf = new_df.groupby(pd.Grouper(key="message")).count()
    pdf = pd.DataFrame()
    pdf["Message"] = gdf.index
    pdf["Count"] = gdf.uuid.values
    pdf = pdf.sort_values(by=["Count"], ascending=False)
    return pdf


def table_of_errors(df):
    columns = [
        TableColumn(field="Message", title="Message"),
        TableColumn(field="Count", title="Count"),
    ]
    table = DataTable(source=ColumnDataSource(error_messages(df)), columns=columns)
    return components(table)
