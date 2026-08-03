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

The process has no inputs and returns the literal output ``status=ok`` when
Rook can execute it. An HTTP health endpoint can delegate to:

.. code-block:: text

   /wps?service=WPS&version=1.0.0&request=Execute&identifier=health

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
