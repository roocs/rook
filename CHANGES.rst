Changes
*******

Unreleased
==========
* Removed cfunits, udunits2, cf-xarray and python-dateutil as dependencies.
* Renamed axes input of ``wps_average.Average`` to dims
* Prepared wps_average to work with daops.ops.average


0.3.1 (2021-02-24)
==================

* Pin ``cf_xarray <0.5.0`` ... does not work with daops/clisops.

0.3.0 (2021-02-24)
==================

* Fixed testdata using git-python (#123).
* Removed xfail where not needed (#121).
* Updated PyWPS 4.4.0 (#120).
* Updated provenance (#112, #114 ,#119).
* Fixed subset alignment (#117).
* ``apply_fixes`` and ``original_files`` option added for WPS processes and the ``Operator`` class (#111).
* Replaced travis with GitHub CI (#104).
* ``director`` module added. This makes decisions on what is returned - NetCDF files or original file URLs (#77, #83)
* ``python-dateutil>=2.8.1`` added as a new dependency.
* Allow no inventory option when processing datasets
* c3s-cmip6 dataset ids must now be identified by the use of ``c3s-cmip6`` (#87).
* Fixed workflow (#79, #75, #71).

0.2.0 (2020-11-19)
==================

Changes:

* Build on cookiecutter template with ``cruft`` update.
* Available processes: ``subset``, ``orchestrate``.
* Using ``daops`` for subsetting operation.
* Using a simple workflow implementation for combining operators.
* Process outputs are provided as ``Metalink`` documents.
* Added initial support for provenance documentation.


0.1.0 (2020-04-03)
==================

* First release.
