from pathlib import Path

import pandas as pd
from pywps import configuration as config
from sqlalchemy import MetaData, Table, create_engine, select

from .base import Usage

CHUNK_SIZE = 10_000


class WPSUsage(Usage):
    def collect(self, time_start=None, time_end=None, outdir=None):
        db_conn = config.get_config_value("logging", "database")
        fname = Path(outdir).joinpath("wps_requests.csv").as_posix()
        engine = create_engine(db_conn)
        try:
            with engine.connect() as connection:
                requests = Table("pywps_requests", MetaData(), autoload_with=connection)
                query = select(requests).where(requests.c.operation == "execute")
                if time_start:
                    query = query.where(
                        requests.c.time_start
                        >= pd.Timestamp(time_start).to_pydatetime()
                    )
                if time_end:
                    query = query.where(
                        requests.c.time_end <= pd.Timestamp(time_end).to_pydatetime()
                    )
                # Stream database results as well as pandas chunks; otherwise
                # some database drivers buffer the full result set themselves.
                chunks = pd.read_sql_query(
                    query,
                    connection.execution_options(yield_per=CHUNK_SIZE),
                    parse_dates=["time_start", "time_end"],
                    chunksize=CHUNK_SIZE,
                )
                with Path(fname).open("w", newline="") as output:
                    for index, chunk in enumerate(chunks):
                        chunk.to_csv(
                            output,
                            index=False,
                            header=index == 0,
                            date_format="%Y-%m-%d %H:%M:%S.%f",
                        )
        finally:
            engine.dispose()
        return fname
