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
dataset's timesteps per year and sizes subset batches toward a configurable
number of timesteps. Configure the target and year limits in ``roocs.ini``:

.. code-block:: ini

   [subset:batching]
   target_timesteps = 2000
   min_batch_years = 1
   max_batch_years = 10
   merge_outputs = true
   merge_target_size = 200MB

When a request produces multiple small batches, Rook merges consecutive files
by using the first batch's on-disk size to estimate how many batches fit within
``merge_target_size``. Rook caps this planning target at
``clisops:write.file_size_limit`` when that limit is configured lower. Because
the estimate is based on one compressed file, the merged file's actual size can
vary. If merging fails, Rook returns the original batch files. Set
``merge_outputs = false`` to always return the individual batch files.


.. _PyWPS: https://pywps.org/
