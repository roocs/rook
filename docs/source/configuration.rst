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

Rook processes long daily and sub-daily subset requests in consecutive
five-year batches after checking whether original files can be returned. To
change the batch size, set the number of years in ``roocs.ini``:

.. code-block:: ini

   [subset]
   time_batch_size = 5

Batching is enabled only when the dataset's ``frequency`` facet is in the
global, case-insensitive allow-list. The defaults can be overridden with:

.. code-block:: ini

   [config_data_types]
   extra_lists = batch_frequencies

   [rook]
   batch_frequencies = day 6hr 6hrPt 3hr 3hrPt 1hr 1hrCM 1hrPt subhrPt


.. _PyWPS: https://pywps.org/
