from roocs_utils.exceptions import InvalidCollection

from rook import CONFIG

from .db import DBCatalog


def get_catalog(project):
    if CONFIG[f"project:{project}"].get("use_catalog"):
        try:
            catalog = DBCatalog(project)
            return catalog
        except Exception:
            raise InvalidCollection()


__all__ = [
    "DBCatalog",
    "get_catalog",
]
