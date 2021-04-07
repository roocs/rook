rook
====

.. image:: https://readthedocs.org/projects/rook-wps/badge/?version=latest
   :target: https://rook-wps.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://github.com/roocs/rook/actions/workflows/main.yml/badge.svg
    :target: https://github.com/roocs/rook/actions
    :alt: Build Status

.. image:: https://img.shields.io/github/license/roocs/rook.svg
    :target: https://github.com/roocs/rook/blob/master/LICENSE.txt
    :alt: GitHub license


rook (the bird)
  *The rook belongs to the crow family ...*

rook
  *Remote Operations On Klimadaten.*

Rook is a Web Processing Service (WPS) of the roocs project
to allow remote operations like subsetting on climate model data.
This service provides a one-to-one mapping to the operations
available in the daops_ library based on xarray.

Documentation
-------------

Learn more about rook in its official documentation at
https://rook-wps.readthedocs.io.

Submit bug reports, questions and feature requests at
https://github.com/roocs/rook/issues

Contributing
------------

You can find information about contributing in our `Developer Guide`_.

Please use bumpversion_ to release a new version.

Tests
-----

The ``tests`` folder includes additional tests for a deployed rook service.

* Smoke test: ensure service is operational. See ``tests/smoke/README.md``.
* Storm test: load-test using locust_. See ``tests/storm/README.md``.

License
-------

Free software: Apache Software License 2.0

Credits
-------

This package was created with Cookiecutter_ and the `bird-house/cookiecutter-birdhouse`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`bird-house/cookiecutter-birdhouse`: https://github.com/bird-house/cookiecutter-birdhouse
.. _`Developer Guide`: https://rook-wps.readthedocs.io/en/latest/dev_guide.html
.. _bumpversion: https://rook-wps.readthedocs.io/en/latest/dev_guide.html#bump-a-new-version
.. _daops: https://github.com/roocs/daops
.. _locust: https://locust.io/
