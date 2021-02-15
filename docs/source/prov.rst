.. _prov:

Provenance
==========

.. contents::
    :local:
    :depth: 1

Introduction
------------

The *rook* processes are recording provenance information about the process execution details.
This information includes:

* used software and versions (rook, daops, ...)
* applied operators like subset or average
* used input data and parameters (cmip6 dataset, time, area)
* generated outputs (netcdf files)
* execution time (start-time and end-time)

This information is described with the `W3C PROV`_ standard and using
the `Python PROV Library`_

Short overview of PROV
----------------------

The `W3C PROV Primer`_ document gives an overview of the `W3C PROV`_ standard.

.. image:: prov-overview.png

Entities
++++++++

W3C PROV
      In PROV, physical, digital, conceptual, or other kinds of thing are called *entities*.

In *rook* we use *entities* for:

* workflow description,
* input datasets and
* resulting output NetCDF files.

Activities
++++++++++

W3C PROV
    *Activities* are how entities come into existence.

In *rook* we use *activities* for:

* operators like ``subset`` and ``average``.
* processes like ``orchestrate`` to run a workflow.

Agent
+++++

W3C PROV
    An *agent* takes a role in an activity.

In *rook* we use *agents* for:

* software like *rook* and *daops*,
* organisations like *Copernicus Climate Data Store*.

Example: Workflow with Subsetting Operators
-------------------------------------------

The rooki_ client for ``rook`` has example notebooks_ for process executions
and displaying the provenance information.

You can run the ``orchestrate`` process to execute a workflow with subsetting operators
and show the provenance document:

.. code-block:: python
  :linenos:
  :emphasize-lines: 14-17

  from rooki import operators as ops
  wf = ops.Subset(
        ops.Subset(
            ops.Input(
                'tas', ['c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.day.tas.gr1.v20190619']
            ),
            time="2016-01-01/2020-12-30",
        ),
        time="2017-01-01/2017-12-30",
  )
  resp = wf.orchestrate()
  # show URLs of output files
  resp.download_urls()
  # show URL to provenance document
  resp.provenance()
  # show URL to provenance image
  resp.provenance_image()

The response of the process includes a provenance document in PROV-JSON_ format:

.. literalinclude:: prov-example.json
  :language: JSON


This provenance document can also be displayed as an image:

.. image:: prov-example.png
   :alt: Provenance Example



Related work in other Projects
------------------------------

The ESMValTool_ project is recording provenance information of scientific workflows run as diagnostics.

The Climate4Impact_ project is using provenance to record the workflow of data staging and creating Jupyter notebooks.

.. _`Python PROV Library`: https://pypi.org/project/prov/
.. _`W3C PROV`: https://www.w3.org/TR/prov-dm/
.. _`W3C PROV Primer`: https://www.w3.org/TR/2013/NOTE-prov-primer-20130430/
.. _PROV-JSON: https://openprovenance.org/prov-json/
.. _rooki: https://rooki.readthedocs.io/en/latest/
.. _notebooks: https://nbviewer.jupyter.org/github/roocs/rooki/tree/master/notebooks/demo/
.. _ESMValTool: https://docs.esmvaltool.org/en/latest/community/diagnostic.html?highlight=provenance#recording-provenance
.. _Climate4Impact: https://is.enes.org/files/C4ISWIRRLTraining.pdf
