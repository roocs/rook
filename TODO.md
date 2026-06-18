# Rook Architecture Cleanup TODO

This document is an unreferenced engineering reminder for future work. It
describes cleanup that should follow the initial Kerchunk, S3, and Zarr support.
Do not treat every item as part of one pull request.

## Current Situation

Rook can partially handle:

- local and catalog-resolved NetCDF files;
- Kerchunk reference files;
- direct S3 paths and S3-backed catalog paths;
- local and S3-backed Zarr stores.

The initial implementations intentionally kept their scope small. As a result,
configuration parsing, storage transport handling, format detection, catalog
resolution, and dataset opening are still spread across modules such as
`rook.__init__`, `rook.catalog`, and `rook.utils.ops.helpers`.

Two structural improvements are desired:

1. Centralize Rook configuration access and parsing.
2. Delegate dataset opening to a common, extensible API.

The cleanup should preserve existing production filesystem and NetCDF behavior.

## Configuration Module

Introduce a central module, probably `rook/config.py`, around the existing
clisops configuration loader. `roocs.ini` should remain the source of truth.

The module should eventually own:

- loading and reloading configuration;
- project configuration lookup;
- parsing booleans and structured JSON options;
- global and project-specific storage roots;
- S3 credentials, endpoint options, and anonymous access;
- validation and useful errors for malformed values;
- protection against accidentally logging secrets.

A small public API is preferable to modules importing a mutable global mapping:

```python
get_config()
reload_config()
get_project_config(project)
get_s3_storage_options()
get_storage_base(project)
```

Keep `rook.CONFIG` temporarily as a compatibility alias during migration. Avoid
an immediate rewrite of every consumer. The current test setup has to replace
captured `CONFIG` references in several modules after reload; central access
should remove that problem.

Do not create a separate credential stack for Zarr. NetCDF, Zarr, and Kerchunk
are data formats, while local filesystems, HTTP, and S3 are transports. S3
transport options should be shared by every compatible format.

## Dataset Opening API

Introduce a focused module such as `rook/io/datasets.py`. It should expose one
common entry point:

```python
open_dataset(source, *, apply_fixes=True) -> xarray.Dataset
```

Internally, separate format detection from transport configuration:

```python
detect_format(source)
open_netcdf(source, storage_options)
open_zarr(source, storage_options)
open_kerchunk(source, storage_options)
```

The implementations should continue using proven upstream behavior where
possible:

- use `clisops.utils.dataset_utils.open_xr_dataset` for existing NetCDF paths;
- use `xarray.open_zarr` for Zarr stores;
- reuse the established clisops/fsspec Kerchunk path;
- pass transport-specific options without duplicating format logic.

Avoid a class hierarchy unless it removes real complexity. A dispatcher plus
small functions or a registry may be sufficient.

## Normalize Dataset Inputs

The current consolidation output mixes scalar references and lists of files.
Consider an internal immutable value object:

```python
@dataclass(frozen=True)
class DatasetSource:
    dataset_id: str | None
    paths: tuple[str, ...]
```

The object should make these rules explicit:

- NetCDF may contain one or many paths;
- Zarr requires one store;
- Kerchunk requires one reference;
- a catalog dataset ID may be eligible for Rook fixes;
- a direct path or URL generally should not trigger project-specific fixes;
- storage options are selected from the paths' transport protocol.

`consolidate()` should eventually resolve collections and paths only. It should
not decide how a format is opened.

## Target Flow

The intended processing flow is:

```text
WPS parameters
    -> catalog and path resolution
    -> DatasetSource
    -> format detection
    -> transport configuration
    -> dataset opener
    -> optional Rook fixes
    -> operation
```

Keep returning original HTTP download URLs separate from paths used internally
for processing. Configuring an S3 processing root must not silently change the
public original-file response behavior.

## Migration Plan

Use small, reviewable pull requests:

1. Add characterization tests for current filesystem NetCDF, Kerchunk, direct
   S3 NetCDF, catalog-backed S3 paths, local Zarr, and S3 Zarr behavior.
2. Introduce `rook/config.py` while preserving `rook.CONFIG` compatibility.
3. Extract existing opening behavior into `rook/io/datasets.py` without changing
   results or configuration semantics.
4. Introduce `DatasetSource` and normalize scalar/list handling internally.
5. Separate format detection from transport option selection.
6. Migrate callers and remove compatibility globals only after coverage exists.

Do not combine unrelated config cleanup, new storage features, and broad catalog
refactoring in a single change.

## Compatibility Requirements

Every cleanup pull request should demonstrate that:

- ordinary local and catalog-resolved NetCDF files still use the established
  clisops opener;
- multi-file NetCDF behavior is unchanged;
- existing project fixes still receive a meaningful catalog dataset ID;
- original-file download URLs remain HTTP/data-node URLs where configured;
- S3 options are only applied to S3-backed inputs;
- missing S3 or Zarr configuration does not alter local filesystem behavior;
- Kerchunk, Zarr, and NetCDF detection is URL-aware and handles query strings;
- malformed optional configuration fails clearly or falls back deliberately,
  rather than being silently misinterpreted.

Always run tests and pre-commit hooks using the existing `rook` conda
environment, for example:

```shell
conda run -n rook pytest ...
conda run -n rook pre-commit run --all-files
```

## Explicitly Deferred Features

These may be useful later but are not prerequisites for the structural cleanup:

- writing operation output directly to S3 or Zarr;
- opening and combining multiple Zarr stores;
- selecting Zarr groups through WPS parameters;
- supporting additional object-store protocols;
- replacing clisops dataset-opening behavior;
- redesigning all of `roocs.ini` at once.
