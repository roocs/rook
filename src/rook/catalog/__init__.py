from roocs_utils.exceptions import InvalidCollection

from .db import DBCatalog
from rook import CONFIG


def get_catalog(project):
    if CONFIG[f"project:{project}"].get("use_catalog"):
        try:
            catalog = DBCatalog(project)
            return catalog
        except Exception:
            raise InvalidCollection()


__all__ = [
    "get_catalog",
    "DBCatalog",
]
