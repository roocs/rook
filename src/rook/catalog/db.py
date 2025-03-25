import sqlalchemy
from daops.catalog.base import Catalog
from daops.catalog.intake import IntakeCatalog
from daops.catalog.util import MAX_DATETIME, MIN_DATETIME, parse_time
from pywps.dblog import get_session
from sqlalchemy import text


class DBCatalog(Catalog):
    def __init__(self, project, url=None):
        super().__init__(project)
        self.table_name = f"rook_catalog_{self.project}".replace("-", "_")
        self.intake_catalog = IntakeCatalog(project, url)

    def exists(self):
        with get_session() as session:
            try:
                engine = session.get_bind()
                ins = sqlalchemy.inspect(engine)
                return ins.dialect.has_table(engine.connect(), self.table_name)
            except Exception:
                return False

    def update(self):
        if not self.exists():
            self.to_db()

    def to_db(self):
        df = self.intake_catalog.load()

        # Handle NaN values and undefined values
        df = df.fillna({"start_time": MIN_DATETIME, "end_time": MAX_DATETIME})
        df = df.replace({"start_time": {"undefined": MIN_DATETIME}})
        df = df.replace({"end_time": {"undefined": MAX_DATETIME}})

        df = df.set_index("ds_id")

        # db connection
        with get_session() as session:
            engine = session.get_bind()
            df.to_sql(
                name=self.table_name,
                con=engine,
                if_exists="replace",
                index=True,
                chunksize=500,
            )
            session.commit()

    def _query(self, collection, time=None, time_components=None):
        """
        Query database to get the given collection (dataset id).
        """
        self.update()
        start, end = parse_time(time, time_components)

        with get_session() as session:
            try:
                # Parameterized query to avoid SQL injection
                if len(collection) > 1:
                    # FIXME: This is vulnerable to SQL injection
                    query_ = text(
                        f"SELECT * FROM {self.table_name} WHERE ds_id IN {tuple(collection)} "
                        f"AND end_time >= :start AND start_time <= :end"
                    )
                    result = session.execute(query_, {
                        # "collection": tuple(collection),
                        "start": start,
                        "end": end
                    }).fetchall()
                else:
                    query_ = text(
                        f"SELECT * FROM {self.table_name} WHERE ds_id = :ds_id "
                        f"AND end_time >= :start AND start_time <= :end"
                    )
                    result = session.execute(query_, {"ds_id": collection[0], "start": start, "end": end}).fetchall()
            except Exception:
                result = []

        # Processing result
        records = {}
        for row in result:
            if row.ds_id not in records:
                records[row.ds_id] = []
            records[row.ds_id].append(row.path)
        return records
