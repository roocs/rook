.. _processes:

Processes
=========

.. contents::
    :local:
    :depth: 1

Health
------

.. autoprocess:: rook.processes.wps_health.Health
    :docstring:
    :skiplines: 1
    :noindex:

The process has no inputs. Its raw output is exactly ``ROOK_HEALTH_OK`` when
Rook can execute it and all configured checks pass. A failed check produces an
OGC exception response containing a concise explanation and does not include
the success marker.

It must be executed synchronously so the health request stays in the web
service and responds immediately instead of being submitted to the batch
system. An HTTP health endpoint can delegate to this synchronous raw-output
request:

.. code-block:: text

   /wps?service=WPS&version=1.0.0&request=Execute&identifier=health&RawDataOutput=status

The monitoring layer should consider the response healthy only when its body
matches ``ROOK_HEALTH_OK`` exactly.

Filesystem availability can be checked by selecting projects in ``roocs.ini``:

.. code-block:: ini

   [health]
   projects = c3s-cordex, c3s-cmip6, c3s-cica-atlas

For each selected project, ``base_dir/.health-check.txt`` is opened and one byte
is read. The ``base_dir`` comes from the existing ``[project:<name>]`` section,
so filesystem paths are not repeated in the health configuration. All selected
projects must be readable. Failure messages identify the project without
exposing the filesystem path. If no projects are configured, only process
execution is checked.

Subset
------

.. autoprocess:: rook.processes.wps_subset.Subset
    :docstring:
    :skiplines: 1
    :noindex:

Average by Time
---------------

.. autoprocess:: rook.processes.wps_average_time.AverageByTime
    :docstring:
    :skiplines: 1
    :noindex:

Average by Dimension
--------------------

.. autoprocess:: rook.processes.wps_average_dim.AverageByDimension
    :docstring:
    :skiplines: 1
    :noindex:

Average by Shape
----------------

.. autoprocess:: rook.processes.wps_average_shape.AverageByShape
    :docstring:
    :skiplines: 1
    :noindex:

Weighted Average
----------------

.. autoprocess:: rook.processes.wps_average_weighted.WeightedAverage
    :docstring:
    :skiplines: 1
    :noindex:

Concat
------

.. autoprocess:: rook.processes.wps_concat.Concat
    :docstring:
    :skiplines: 1
    :noindex:

Regrid
------

.. autoprocess:: rook.processes.wps_regrid.Regrid
    :docstring:
    :skiplines: 1
    :noindex:

Orchestrate
-----------

.. autoprocess:: rook.processes.wps_orchestrate.Orchestrate
    :docstring:
    :skiplines: 1
    :noindex:

Usage
-----

.. autoprocess:: rook.processes.wps_usage.Usage
    :docstring:
    :skiplines: 1
    :noindex:

Dashboard
---------

.. autoprocess:: rook.processes.wps_dashboard.DashboardProcess
    :docstring:
    :skiplines: 1
    :noindex:
