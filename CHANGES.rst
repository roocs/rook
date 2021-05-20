Changes
*******

0.6.0 (2021-05-20)
==================

* Inventory urls removed from ``etc/roocs.ini``. Intake catalog url now lives in daops. (#175)
* Intake catalog base and search functionality moved to daops. Database intake implementation remains in rook. (#175)
* Updated to roocs-utils 0.4.2.
* Updated to clisops 0.6.4.
* Updated to daops 0.6.0.
* Added initial usage process (#178)


0.5.0 (2021-04-01)
==================

* Updated pywps 4.4.2.
* Updated clisops 0.6.3.
* Updated roocs-utils 0.3.0.
* Use ``FileMapper`` for search results (#169).
* Using intake catalog (#148).

0.4.2 (2021-03-22)
==================

* Updated clisops 0.6.2

0.4.1 (2021-03-21)
==================

* Updated pywps 4.4.1 (#162, #154, #151).
* Use pywps ``storage_copy_function=link`` (#154).
* Updated director with InvalidCollection error (#153).
* Added locust (storm) tests (#141, #149, #155).
* Updated smoke tests (#134, #137).
* Cleaned requirements (#152).
* Fixed warning in workflow yaml loaded (#142).
* Removed original files option for average and added test (#136).

0.4.0 (2021-03-04)
==================

* Removed cfunits, udunits2, cf-xarray and python-dateutil as dependencies.
* Use daops>=0.5.0
* Renamed axes input of ``wps_average.Average`` to dims
* Added wps_average to work with daops.ops.average (#126)
* Fixed tests for new inventory (#127)
* Use ``apply_fixes=False`` for average (#129)
* Added smoke tests (#131, #134)

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
