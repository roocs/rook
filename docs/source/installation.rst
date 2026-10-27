.. _installation:

Installation
============

.. contents::
    :local:
    :depth: 1

Updating certificate security dependencies
------------------------------------------

The `Python eMudhra / emSign advisory`_ requires updated CA bundles and package
installers. Rook's environment files require ``certifi`` and ``ca-certificates``
2026.10.23 or newer, and ``pip`` 26.2.2 or newer. The development environment also
requires ``virtualenv`` 21.14.12 or newer so newly created environments use a
patched certificate bundle.

Update the Conda installation that creates environments first (usually ``base``).
For Miniforge / conda-forge:

.. code-block:: console

   $ conda install -n base -c conda-forge "conda>=26.9.4" "certifi>=2026.10.23" "ca-certificates>=2026.10.23"

Then update each existing Rook environment; changing repository requirements does
not update installed environments:

.. code-block:: console

   $ conda env update -n rook -f environment.yml
   $ conda activate rook
   $ python -m pip install --upgrade -e .
   $ python -m pip check
   $ conda list '^(python|pip|certifi|ca-certificates)$'

Apply ``environment-dev.yml`` or ``environment-docs.yml`` as well if used.
For pip-only environments, first bootstrap patched pip using the checksum-pinned
wheel command in the Python advisory, then run:

.. code-block:: console

   $ python -m pip install --upgrade "pip>=26.2.2" "certifi>=2026.10.23"
   $ python -m pip install --upgrade -e ".[dev]"

Upgrade separately installed ``uv`` to at least 0.13.4 if used. Updating certifi
alone does not update pip's or uv's bundled trust stores. Also update your OS and
any custom CA bundles. For Python's additional intermediate-certificate blocking,
use Python 3.11.18, 3.12.16, 3.13.18, 3.14.10, or a newer patched release.

Regenerate deployment locks with ``make conda-spec`` after changing dependencies.
Rebuild and redeploy container images with a fresh base and no layer cache:

.. code-block:: console

   $ docker build --pull --no-cache -t roocs/rook .

.. _Python eMudhra / emSign advisory: https://discuss.python.org/t/information-for-python-users-regarding-emudhra-emsign-ca-certificate-security-incident/109576

Install from GitHub
-------------------

Check out code from the rook GitHub repo and start the installation:

.. code-block:: console

   $ git clone https://github.com/roocs/rook.git
   $ cd rook

Create Conda environment named `rook`:

.. code-block:: console

   $ conda env create -f environment.yml
   $ conda activate rook

Install rook app:

.. code-block:: console

   $ pip install -e .
   OR
   $ make install

For development you can use this command:

.. code-block:: console

   $ pip install -e .[dev]
   OR
   $ make develop

Start rook PyWPS service
------------------------

After successful installation you can start the service using the ``rook`` command-line.

.. code-block:: console

   $ rook --help # show help
   $ rook start  # start service with default configuration

   OR

   $ rook start --daemon # start service as daemon
   loading configuration
   forked process id: 42

The deployed WPS service is by default available on:

http://localhost:5000/wps?service=WPS&version=1.0.0&request=GetCapabilities.

.. NOTE:: Remember the process ID (PID) so you can stop the service with ``kill PID``.

You can find which process uses a given port using the following command (here for port 5000):

.. code-block:: console

   $ lsof -i :5000


Check the log files for errors:

.. code-block:: console

   $ tail -f  pywps.log

... or do it the lazy way
+++++++++++++++++++++++++

You can also use the ``Makefile`` to start and stop the service:

.. code-block:: console

   $ make start
   $ make status
   $ tail -f pywps.log
   $ make stop


Run rook as Docker container
----------------------------

You can also run rook as a Docker container.

Build and run the image directly:

.. code-block:: console

   $ docker build -t roocs/rook .
   $ docker run --rm -p 5000:5000 roocs/rook

Or use Docker Compose:

.. code-block:: console

   $ docker compose build
   $ docker compose up

Stop the service with ``Ctrl+C``, then remove the stack with:

.. code-block:: console

   $ docker compose down

Use Ansible to deploy rook on your System
-----------------------------------------

Use the `Ansible playbook`_ for PyWPS to deploy rook on your system.


.. _Ansible playbook: https://ansible-wps-playbook.readthedocs.io/en/latest/index.html
