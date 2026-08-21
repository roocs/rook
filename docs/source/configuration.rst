.. _configuration:

Configuration
=============

Command-line options
--------------------

You can overwrite the default `PyWPS`_ configuration by using command-line options.
See the rook help which options are available:

.. code-block:: console

    $ rook start --help
    --hostname HOSTNAME        hostname in PyWPS configuration.
    --port PORT                port in PyWPS configuration.

Start service with different hostname and port:

.. code-block:: console

    $ rook start --hostname localhost --port 5001

Use a custom configuration file
-------------------------------

You can overwrite the default `PyWPS`_ configuration by providing your own
PyWPS configuration file (just modify the options you want to change).
Use one of the existing ``sample-*.cfg`` files as example and copy them to ``etc/custom.cfg``.

For example change the hostname (*demo.org*) and logging level:

.. code-block:: console

   $ cd rook
   $ vim etc/custom.cfg
   $ cat etc/custom.cfg
   [server]
   url = http://demo.org:5000/wps
   outputurl = http://demo.org:5000/outputs

   [logging]
   level = DEBUG

Start the service with your custom configuration:

.. code-block:: console

   # start the service with this configuration
   $ rook start -c etc/custom.cfg


Fix provider backend
--------------------

Rook chooses the dataset fix provider internally from the ``roocs.ini``
configuration. The default backend is ``woodpecker``.

To use the legacy fixes, set:

.. code-block:: ini

   [fixes]
   backend = legacy

Supported values are ``legacy`` and ``woodpecker``.


Subset time batching
--------------------

After checking whether original files can be returned, Rook estimates the
dataset's timesteps per year and decoded bytes per timestep. It applies both a
configurable timestep ceiling and an approximate process-memory ceiling; the
stricter target determines the batch length. Configure the targets and year
limits in ``roocs.ini``:

.. code-block:: ini

   [subset:batching]
   target_timesteps = 2000
   memory_limit = 4GB
   min_batch_years = 1
   max_batch_years = 10
   merge_outputs = true
   merge_target_size = 200MB

``memory_limit`` defaults to ``4GB`` and can be set by deployment tooling to
match the Slurm job allocation. The estimate reserves half of that limit for
Xarray, Dask, and NetCDF writer overhead. It is a planning aim rather than a
hard runtime memory limit. If one minimum-size batch exceeds the aim, Rook still
uses ``min_batch_years``.

When a request produces multiple small batches, Rook merges consecutive files
by using the first batch's on-disk size to estimate how many batches fit within
``merge_target_size``. Rook caps this planning target at
``clisops:write.file_size_limit`` when that limit is configured lower. Because
the estimate is based on one compressed file, the merged file's actual size can
vary. If merging fails, Rook returns the original batch files. Set
``merge_outputs = false`` to always return the individual batch files.

Concat time batching
--------------------

CMIP6-decadal concat uses a separate, conservative adaptive batching target. By
default, concat batches are capped at one year so full unconstrained requests
are written incrementally. Its memory estimate multiplies one realization's
decoded temporal payload by the number of ensemble members before applying the
same 2x writer-overhead estimate used for subset. These settings do not affect
subset batching.

.. code-block:: ini

   [concat:batching]
   target_timesteps = 365
   memory_limit = 4GB
   min_batch_years = 1
   max_batch_years = 1

When the combined ensemble estimate cannot fit a full year, concat switches to
coordinate-aligned subannual batches capped by the effective timestep target.
If even one combined timestep exceeds ``memory_limit``, Rook logs a warning so
the Slurm allocation or spatial pushdown can be adjusted.

Processing diagnostics
----------------------

Explicit post-batch memory cleanup is configured in the general diagnostics
section:

.. code-block:: ini

   [diagnostics]
   free_memory = false

Set ``free_memory = true`` to run both ``gc.collect()`` and ``malloc_trim(0)``
after each concat batch. Explicit cleanup remains disabled by default because it
did not materially reduce the observed retained memory. Normal dataset closing
and reference dropping are always performed. The
``ROOK_DIAGNOSTIC_MALLOC_TRIM`` environment variable overrides this setting.


.. _PyWPS: https://pywps.org/
