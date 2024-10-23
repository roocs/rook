import pandas as pd
from bokeh.models import ColumnDataSource, DataTable, DateFormatter, TableColumn

from .base import TableView


class MessageTable(TableView):
    def data(self):
        edf = self.df.loc[self.df["status"] == 5]
        gdf = edf.groupby(pd.Grouper(key="message"))
        adf = gdf.agg(
            First=("time_start", "min"),
            Last=("time_start", "max"),
            Count=("uuid", "count"),
        )
        pdf = pd.DataFrame()
        pdf["Message"] = adf.index
        pdf["First"] = adf.First.dt.date.values
        pdf["Last"] = adf.Last.dt.date.values
        pdf["Count"] = adf.Count.values
        pdf = pdf.sort_values(by=["Last"], ascending=False)
        return pdf

    def table(self):
        date_fmt = DateFormatter(format="%Y-%m-%d")
        columns = [
            TableColumn(field="Message", title="Message"),
            TableColumn(field="First", title="First", formatter=date_fmt),
            TableColumn(field="Last", title="Last", formatter=date_fmt),
            TableColumn(field="Count", title="Count"),
        ]
        table = DataTable(source=ColumnDataSource(self.data()), columns=columns)
        return table
