"""A WPS service for roocs."""

###################################################################################
# Apache Software License 2.0
#
# Copyright (c) 2024, Carsten Ehbrecht, Eleanor Smith, Ag Stephens
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###################################################################################

from .__version__ import __author__, __email__, __version__  # noqa: F401

from clisops.config import get_config


# Workaround for clisops to not re-import rook
class Package:
    __file__ = __file__  # noqa


package = Package()
CONFIG = get_config(package)

from .wsgi import application  # noqa: F401
