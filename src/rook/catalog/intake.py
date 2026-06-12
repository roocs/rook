"""Utilities for working with Intake catalogs."""

from urllib.parse import urlparse

import fsspec
import intake

from rook import CONFIG

from .base import Catalog
from .util import MAX_DATETIME, MIN_DATETIME, parse_time

DEFAULT_INTAKE_CATALOG_URL = (
    "https://raw.githubusercontent.com/cp4cds/c3s_34g_manifests/master/"
    "intake/catalogs/c3s.yaml"
)


class IntakeCatalog(Catalog):
    """Intake catalog class."""

    def __init__(self, project, url=None):
        super().__init__(project)
        self.url = (
            url
            or CONFIG.get("catalog", {}).get("intake_catalog_url")
            or DEFAULT_INTAKE_CATALOG_URL
        )
        self._cat = None
        self._store = {}

    @property
    def catalog(self):
        """Return the intake catalog."""
        if not self._cat:
            parsed_url = urlparse(self.url)
            is_http_catalog = parsed_url.scheme in {"http", "https"}

            if is_http_catalog:
                fs = fsspec.filesystem("http", client_kwargs={"trust_env": True})
                try:
                    self._cat = intake.open_catalog(self.url, fs=fs)
                except TypeError:
                    # Keep compatibility with intake variants that do not accept fs.
                    self._cat = intake.open_catalog(self.url)
            else:
                self._cat = intake.open_catalog(self.url)
        return self._cat

    def load(self):
        """Load the catalog."""
        if self.project not in self._store:
            project_catalog = self.catalog[self.project]

            # Avoid stale transport options on nested catalogs for some partner deployments.
            if hasattr(project_catalog, "_storage_options"):
                project_catalog._storage_options = None

            self._store[self.project] = project_catalog.read()
        return self._store[self.project]

    def _query(self, collection, time=None, time_components=None):
        df = self.load()
        start, end = parse_time(time, time_components)

        # workaround for NaN values when no time axis (fx datasets)
        df = df.fillna({"start_time": MIN_DATETIME, "end_time": MAX_DATETIME})

        # needed when catalog created from catalog_maker instead of above - can remove above line eventually
        df = df.replace({"start_time": {"undefined": MIN_DATETIME}})
        df = df.replace({"end_time": {"undefined": MAX_DATETIME}})

        # search
        result = df.loc[
            (df.ds_id.isin(collection))
            & (df.end_time >= start)
            & (df.start_time <= end)
        ]
        records = {}
        for _, row in result.iterrows():
            if row.ds_id not in records:
                records[row.ds_id] = []
            records[row.ds_id].append(row.path)
        return records
