from rook.exceptions import InvalidCollection

from .intake import IntakeCatalog
from .db import DBCatalog


def get_catalog(project):
    if project == "c3s-cmip6":
        catalog = DBCatalog(project)
    else:
        raise InvalidCollection()
    return catalog


__all__ = [
    get_catalog,
    IntakeCatalog,
    DBCatalog,
]
