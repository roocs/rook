# -*- coding: utf-8 -*-

"""Top-level package for rook."""

from roocs_utils.config import get_config

import rook

from .__version__ import __author__, __email__, __version__  # noqa: F401

CONFIG = get_config(rook)

from .wsgi import application  # noqa: F401
