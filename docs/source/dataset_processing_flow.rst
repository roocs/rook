.. _dataset_processing_flow:

Dataset Processing Flow
=======================

This page documents the request decision tree that remains after the director
cleanup. There is no longer a ``Director`` class; the name now refers to the
small wrapper around request planning and execution used by WPS processes.

Director Decision Tree
----------------------

.. mermaid::

   flowchart TD
       Entry["WPS process or workflow stage"] --> Operator["Operator.call(args)"]
       Operator --> DirectFiles{"collection is a file list?"}

       DirectFiles -- yes --> DirectMapper["Resolve paths and build FileMapper"]
       DirectMapper --> DirectRunner["Run operation runner directly"]

       DirectFiles -- no --> Wrap["wrap_director(collection, inputs, runner)"]
       Wrap --> Plan["plan_request(collection, inputs)"]
       Plan --> Project["resolve_project(collection[0])"]
       Project --> CatalogEnabled{"project uses catalog?"}

       CatalogEnabled -- no --> NoCatalogPlan["RequestPlan(project only)"]
       NoCatalogPlan --> ExecuteOperation

       CatalogEnabled -- yes --> CatalogSearch["get_catalog(project)\ncatalog.search(collection, time, time_components)"]
       CatalogSearch --> ValidSearch{"all requested collections found?"}
       ValidSearch -- no --> InvalidCollection["InvalidCollection -> ProcessError"]
       ValidSearch -- yes --> OriginalRequested{"original_files requested\nor project is c3s-ipcc-atlas?"}

       OriginalRequested -- yes --> OriginalPlan["original_files_plan\nuse catalog download URLs"]
       OriginalRequested -- no --> MustProcess{"operation must process?\ndims, freq, or grid present"}

       MustProcess -- yes --> OperationPlan["operation_plan\nbuild FileMapper dataset sources"]
       MustProcess -- no --> Aligned{"subset aligns with whole files?"}
       Aligned -- yes --> AlignedOriginalPlan["original_files_plan\nuse aligned download URLs"]
       Aligned -- no --> OperationPlan

       OriginalPlan --> CollectOriginal["collect original file URIs"]
       AlignedOriginalPlan --> CollectOriginal
       CollectOriginal --> Result["RequestResult.output_uris"]

       OperationPlan --> ExecuteOperation["prepare_operation_inputs\nclean inputs and replace collection when planned"]
       ExecuteOperation --> Runner["Run operation runner"]
       DirectRunner --> Consolidate["Operation consolidates collection"]
       Runner --> Consolidate
       Consolidate --> Sources["DatasetSource values"]
       Sources --> Open["Detect format and transport\nNetCDF, Zarr, Kerchunk\nfilesystem, HTTP, S3, reference"]
       Open --> Fixes["Apply catalog-specific dataset fixes\nwhen a dataset_id is present"]
       Fixes --> Process["subset, average, regrid, concat, or weighted average"]
       Process --> Result

Decision Ownership
------------------

``rook.operations.execution.Operator.call`` decides whether a request is already
a file list from a previous workflow step. Those requests bypass catalog
planning and run the operation runner directly with a ``FileMapper``.

``rook.director.planning.plan_request`` handles catalog-backed requests. It
resolves the project, validates catalog search results, and chooses between an
original-file response and operation execution.

``rook.director.execution.execute_plan`` adapts the plan into output URIs. It
collects original file URLs when processing is skipped, otherwise it prepares
operation inputs and calls the operation runner.

``rook.operations.consolidate`` converts operation collections into
``DatasetSource`` values. It keeps direct Zarr, Kerchunk, and S3 inputs out of
catalog lookup, resolves catalog-backed NetCDF datasets to files, and preserves
dataset IDs where they are needed for dataset fixes.

``rook.io.datasets`` owns format and transport detection, storage options, and
dataset opening. Catalog-specific fixes are applied only when a ``DatasetSource``
has a dataset ID.
