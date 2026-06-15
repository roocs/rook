====
rook
====


+----------------------------+-----------------------------------------------------+
| Versions                   | |pypi| |conda| |versions|                           |
+----------------------------+-----------------------------------------------------+
| Documentation and Support  | |docs| |gitter|                                     |
+----------------------------+-----------------------------------------------------+
| Open Source                | |license|                                           |
| Coding Standards           | |ruff| |prek| |pre-commit-ci|                       |
+----------------------------+-----------------------------------------------------+
| Development Status         | |status| |build|                                    |
+----------------------------+-----------------------------------------------------+

rook (the bird)
  *An intelligent and social bird that surveys vast landscapes,
  finds what matters, and brings it within easy reach.*

rook
  *Remote Operations On Klimadaten.*

Rook: Smart access to climate data.

Like the bird, Rook surveys vast climate archives, finds what
matters, and brings it within easy reach.

Rook is a service of the roocs project that provides remote
operations for large climate datasets.

The processing operations are implemented in Python on top of
xarray and the `clisops`_ library, enabling efficient subsetting,
averaging, and extraction of climate data from archives such as
CMIP and CORDEX.

Rook in a Minute
----------------

Get a local service running with the minimal setup:

.. code-block:: console

        $ git clone https://github.com/roocs/rook.git
        $ cd rook
        $ conda env create -f environment.yml
        $ conda activate rook
        $ make develop
        $ make start

Then test the service endpoint in your browser:

https://localhost:5000/wps?service=WPS&version=1.0.0&request=GetCapabilities

Use ``make stop`` to stop the local service.

Documentation
-------------

Learn more about Rook in its official documentation at https://rook-wps.readthedocs.io.

Submit bug reports, questions, and feature requests at https://github.com/roocs/rook/issues

Contributing
------------

You can find information about contributing in our `Developer Guide`_.

Use bump-my-version_ to release a new version.

Tests
-----

The tests folder includes additional tests for deployed Rook services.

* Smoke test: ensure the service is operational. See tests/smoke/README.md.
* Storm test: load-test using locust. See tests/storm/README.md.


License
-------

* Free software: Apache Software License 2.0
* Documentation: https://rook-wps.readthedocs.io.


Credits
-------

This package was created with Cookiecutter_ and the `bird-house/cookiecutter-birdhouse`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`bird-house/cookiecutter-birdhouse`: https://github.com/bird-house/cookiecutter-birdhouse
.. _`clisops`: https://github.com/roocs/clisops/tree/master
.. _`Developer Guide`: https://rook-wps.readthedocs.io/en/latest/dev_guide.html
.. _bump-my-version: https://rook-wps.readthedocs.io/en/latest/dev_guide.html#bump-a-new-version

.. |build| image:: https://github.com/roocs/rook/actions/workflows/main.yml/badge.svg
        :target: https://github.com/roocs/rook/actions/workflows/main.yml
        :alt: Build Status

.. |conda| image:: https://img.shields.io/conda/vn/conda-forge/rook.svg
        :target: https://anaconda.org/conda-forge/rook
        :alt: Conda-forge Build Version

.. |docs| image:: https://readthedocs.org/projects/rook/badge/?version=latest
        :target: https://rook-wps.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status

.. |gitter| image:: https://badges.gitter.im/bird-house/birdhouse.svg
        :target: https://gitter.im/bird-house/birdhouse
        :alt: Bird-house Gitter Chat

.. |license| image:: https://img.shields.io/github/license/roocs/rook.svg
        :target: https://github.com/roocs/rook/blob/main/LICENSE.txt
        :alt: License

.. |pypi| image:: https://img.shields.io/pypi/v/rook.svg
        :target: https://pypi.python.org/pypi/rook
        :alt: Python Package Index Build

.. |pre-commit-ci| image:: https://results.pre-commit.ci/badge/github/roocs/rook/main.svg
        :target: https://results.pre-commit.ci/latest/github/roocs/rook/main
        :alt: pre-commit.ci status

.. |prek| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/j178/prek/master/docs/assets/badge-v0.json
        :target: https://github.com/j178/prek
        :alt: prek

.. |ruff| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
        :target: https://github.com/astral-sh/ruff
        :alt: Ruff

.. |status| image:: https://www.repostatus.org/badges/latest/wip.svg
        :alt: Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.
        :target: https://www.repostatus.org/#wip

.. |versions| image:: https://img.shields.io/pypi/pyversions/rook.svg
        :target: https://pypi.python.org/pypi/rook
        :alt: Supported Python Versions
