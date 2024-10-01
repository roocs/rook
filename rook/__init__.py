"""Top-level package for rook."""

from .__version__ import __author__, __email__, __version__  # noqa: F401

from roocs_utils.config import get_config


# Workaround for roocs_utils to not re-import rook
class Package:
    __file__ = __file__  # noqa


package = Package()
CONFIG = get_config(package)

from .wsgi import application  # noqa: F401
