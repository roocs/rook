# -*- coding: utf-8 -*-

"""Unit test package for rook."""
import os

from .common import ROOCS_CFG, write_roocs_cfg

# create roocs config for testing
write_roocs_cfg()
# point to roocs cfg in environment
os.environ['ROOCS_CONFIG'] = ROOCS_CFG
