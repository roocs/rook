from clisops.exceptions import InvalidCollection

from rook import config

from .db import DBCatalog


def get_catalog(project):
    if config.get_project_config(project).get("use_catalog"):
        try:
            catalog = DBCatalog(project)
            return catalog
        except Exception:
            raise InvalidCollection()


__all__ = [
    "DBCatalog",
    "get_catalog",
]
