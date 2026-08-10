.. _devguide:

Developer Guide
===============

.. contents::
    :local:
    :depth: 1

.. WARNING:: To create new processes look at examples in Emu_.

Building the docs
-----------------

First install dependencies for the documentation:

.. code-block:: console

    $ make develop

Run the Sphinx docs generator:

.. code-block:: console

    $ make docs

.. _testing:

Running tests
-------------

Run tests using pytest_.

First activate the ``rook`` Conda environment and install ``pytest``.

.. code-block:: console

    $ source activate rook
    $ pip install -r requirements_dev.txt  # if not already installed
    OR
    $ make develop

Run default local tests (skip smoke and online):

.. code-block:: console

    $ pytest -v -m "not smoke and not online"

Run smoke tests against a deployed production service only:

.. code-block:: console

    $ pytest -v -m "smoke" tests/smoke

Run all tests:

.. code-block:: console

    $ pytest -v

Run lint checks:

.. code-block:: console

    $ ruff check src/rook tests

Run tests the lazy way
----------------------

Do the same as above using the ``Makefile``.

.. code-block:: console

    $ make test
    $ make smoke
    $ make lint

Prepare a release
-----------------

Update the Conda lock and specification files used to build identical
environments_ on a specific OS.

.. note:: You should run this on your target OS, in our case Linux.

.. code-block:: console

    $ conda activate rook
    $ make conda-spec

Deployment configuration should use ``linux-64.spec`` directly.

.. _environments: https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#building-identical-conda-environments


Bump a new version
------------------

Make a new version of rook in the following steps:

* Prepare the change on a release branch.
* Update ``CHANGELOG.rst`` with the next version.
* Dry run: ``bump-my-version bump --dry-run --verbose --new-version 1.2.4 patch``.
* Create the release commit: ``bump-my-version bump --new-version 1.2.4 patch``.
* Push the branch and merge the release commit through the normal review flow.
* Update local ``main``: ``git switch main && git pull --ff-only``.
* Tag the merged commit: ``git tag -a v1.2.4 -m "Release v1.2.4"``.
* Push the tag: ``git push origin v1.2.4``.

``bump-my-version`` updates and commits the version metadata but deliberately
does not create the tag. Creating it after the merge ensures the release tag
identifies the exact commit deployed from ``main``.

See the bump-my-version_ documentation for details.

.. _bump-my-version: https://pypi.org/project/bump-my-version/
.. _pytest: https://docs.pytest.org/en/latest/
.. _Emu: https://github.com/bird-house/emu
