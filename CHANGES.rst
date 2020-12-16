Changes
*******

Unreleased
==========
* ``apply_fixes`` and ``original_files`` option added for WPS processes and the ``Operator`` class.
* ``director`` module added. This makes decisions on what is returned - NetCDF files or original file URLs.

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
