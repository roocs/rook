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
    $ python -m pip install --group dev
    $ python -m pip install --editable .
    # or
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


Deploying
---------

A reminder for the maintainers on how to deploy a new version.

* Make sure all code changes have been committed and pushed to `main` (including an entry in CHANGELOG.rst).
* Create a new branch and Pull Request (`prepare-release-vX.Y.Z`).
* Update ``CHANGELOG.rst`` history under `unreleased`.
* Dry run: ``bump-my-version bump major|minor|patch|build --dry-run --verbose``
* Do it for real: ``bump-my-version bump major|minor|patch``
* Prepare release version: ``bump-my-version bump release``
* Push it: ``git push``
* Merge your Pull Request to `main`.
* Tag the last commit on `main`.

GitHub Workflow automation should then prepare a deployment to Docker Hub and to `TestPyPI`.
Once the version has been published, the next deployment will then be to the official `PyPI`.

See the bump-my-version_ documentation for details.

.. _bump-my-version: https://pypi.org/project/bump-my-version/
.. _pytest: https://docs.pytest.org/en/latest/
.. _Emu: https://github.com/bird-house/emu
