import pandas as pd
from bokeh.models import ColumnDataSource
from bokeh.models import TableColumn, DataTable

from .base import TableView
from ..models import concurrent_requests


class OverviewTable(TableView):
    def __init__(self, df, df_downloads):
        super().__init__(df)
        self.df_downloads = df_downloads

    def data(self):
        # requests
        total = self.df.uuid.count()
        failed = self.df.loc[self.df["status"] == 5].uuid.count()
        # requests per day
        counts = self.df.groupby(pd.Grouper(key="time_start", freq="1D")).uuid.count()
        # duration
        duration = self.df["time_end"] - self.df["time_start"]
        duration = duration.dt.seconds
        duration = duration[lambda x: x > 0]
        # concurrency
        cdf = concurrent_requests(self.df)
        running = cdf.groupby(pd.Grouper(key="time", freq="1D")).running.max()
        # downloads
        downloads = self.df_downloads.groupby(
            pd.Grouper(key="datetime", freq="1D")
        ).request_type.count()
        # data transfer
        tdf = self.df_downloads.groupby(pd.Grouper(key="datetime", freq="1D")).sum()
        tdf["size"] = tdf["size"].apply(lambda x: x / 1024 ** 3)
        transfer = tdf["size"]
        data_ = dict(
            property=[
                "Total Requests",
                "Failed Requests",
                "Requests per day (min/max/median)",
                "Duration (min/max/median)",
                "Concurrency per day (min/max/median)",
                "Downloads per day (min/max/median)",
                "Data transfer per day (min/max/median)",
                "Total data transfer",
                "Data transfer per request",
            ],
            value=[
                total,
                failed,
                f"{counts.min()} / {counts.max()} / {counts.median()}",
                f"{duration.min()} / {duration.max()} / {duration.median()}",
                f"{running.min()} / {running.max()} / {running.median()}",
                f"{downloads.min()} / {downloads.max()} / {downloads.median()}",
                f"{transfer.min():.2f} GB / {transfer.max():.2f} GB / {transfer.median():.2f} GB",
                f"{transfer.sum():.2f} GB",
                f"{transfer.sum() / (total - failed):.2f} GB",
            ],
        )
        return data_

    def table(self):
        columns = [
            TableColumn(field="property", title="Property"),
            TableColumn(field="value", title="Value"),
        ]
        table = DataTable(source=ColumnDataSource(self.data()), columns=columns)
        return table
