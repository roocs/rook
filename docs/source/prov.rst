.. _prov:

Provenance
==========

.. contents::
    :local:
    :depth: 1

Overview
--------

The ``rook`` processes are collecting provenance information about the process execution details.
This information includes:

* used software and versions
* applied operators
* used input data and parameters
* generated outputs
* execution time (start-time and end-time)

This information is described with the `W3C Provenance`_ standard and using
the `Python PROV Library`_



Example: Workflow with Subsetting Operators
-------------------------------------------

The rooki_ client for ``rook`` has example notebooks_ for process executions
and displaying the provenance information.

You can run the ``orchestrate`` process to execute a workflow with subsetting operators:

.. code-block:: python

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

The response of the process includes a provenance document in PROV-JSON format:

.. literalinclude:: prov-example.json
  :language: JSON


This document can also be displayed as an image:

.. figure:: prov-example.png
   :alt: Provenance Example

   Provenance information displayed as an image.


Related work in other Projects
------------------------------

The ESMValTool_ project is recording provenance information of scientific workflows run as diagnostics.

The Climate4Impact_ project is using provenance to record the workflow of data staging and creating Jupyter notebooks.

.. _`Python PROV Library`: https://pypi.org/project/prov/
.. _`W3C Provenance`: https://www.w3.org/TR/prov-dm/
.. _rooki: https://rooki.readthedocs.io/en/latest/
.. _notebooks: https://nbviewer.jupyter.org/github/roocs/rooki/tree/master/notebooks/demo/
.. _ESMValTool: https://docs.esmvaltool.org/en/latest/community/diagnostic.html?highlight=provenance#recording-provenance
.. _Climate4Impact: https://is.enes.org/files/C4ISWIRRLTraining.pdf
