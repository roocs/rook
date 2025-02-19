import sqlalchemy
from daops.catalog.base import Catalog
from daops.catalog.intake import IntakeCatalog
from daops.catalog.util import MAX_DATETIME, MIN_DATETIME, parse_time
from pywps.dblog import get_session


class DBCatalog(Catalog):
    def __init__(self, project, url=None):
        super().__init__(project)
        self.table_name = f"rook_catalog_{self.project}".replace("-", "_")
        self.intake_catalog = IntakeCatalog(project, url)

    def exists(self):
        session = get_session()
        engine = get_session().get_bind()
        try:
            ins = sqlalchemy.inspect(engine)
            exists_ = ins.dialect.has_table(engine.connect(), self.table_name)
        except Exception:
            exists_ = False
        finally:
            session.close()
        return exists_

    def update(self):
        if not self.exists():
            self.to_db()

    def to_db(self):
        df = self.intake_catalog.load()
        # workaround for NaN values when no time axis (fx datasets)
        df = df.fillna({"start_time": MIN_DATETIME, "end_time": MAX_DATETIME})

        # needed when catalog created from catalog_maker instead of above - can remove the above eventually
        df = df.replace({"start_time": {"undefined": MIN_DATETIME}})
        df = df.replace({"end_time": {"undefined": MAX_DATETIME}})

        df = df.set_index("ds_id")

        # db connection
        session = get_session()
        try:
            # FIXME: This pattern is deprecated in Pandas v2.0+
            df.to_sql(
                name=self.table_name,
                con=session.connection(),
                schema=None,
                if_exists="replace",
                index=True,
                chunksize=500,
            )
            session.commit()
        finally:
            session.close()

    def _query(self, collection, time=None, time_components=None):
        """
        Query database to get the given collection (dataset id).

        https://stackoverflow.com/questions/8603088/sqlalchemy-in-clause
        """
        self.update()
        start, end = parse_time(time, time_components)

        session = get_session()
        try:
            if len(collection) > 1:
                # FIXME: This is vulnerable to SQL injection
                query_ = (
                    f"SELECT * FROM {self.table_name} WHERE ds_id IN {tuple(collection)} "  # noqa: S608
                    f"and end_time>='{start}' and start_time<='{end}'"  # noqa: S608
                )

            else:
                # FIXME: This is vulnerable to SQL injection
                query_ = (  # noqa: S608
                    f"SELECT * FROM {self.table_name} WHERE ds_id='{collection[0]}' "  # noqa: S608
                    f"and end_time>='{start}' and start_time<='{end}'"  # noqa: S608
                )
            result = session.execute(query_).fetchall()

        except Exception:
            result = []
        finally:
            session.close()
        records = {}
        for row in result:
            if row.ds_id not in records:
                records[row.ds_id] = []
            records[row.ds_id].append(row.path)
        return records
