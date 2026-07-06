.. _dataset_processing_flow:

Dataset Processing Flow
=======================

This page documents the request decision tree that remains after the director
cleanup. There is no longer a ``Director`` class; the name now refers to the
small wrapper around request planning and execution used by WPS processes.

The diagram is written as a blueprint for a future reimplementation: first
decide what kind of input was received, then decide whether catalog metadata is
needed, then choose between returning existing files and running an operation.

Director Decision Tree
----------------------

.. mermaid::

   flowchart TD
       Start(["Request arrives from a WPS process<br/>or workflow stage"])

       subgraph Input["1. Understand the input"]
           Start --> HasFiles{"Do we already have concrete files<br/>from an earlier workflow step?"}
           HasFiles -- yes --> DirectFiles["Normalize those files<br/>and run the requested operation"]
           HasFiles -- no --> Project["Read the project from<br/>the requested collection id"]
       end

       subgraph Catalog["2. Resolve catalog data when needed"]
           Project --> UsesCatalog{"Does this project use<br/>a Rook catalog?"}
           UsesCatalog -- no --> PlainOperation["Keep the original collection<br/>and run the operation"]
           UsesCatalog -- yes --> Search["Search the catalog<br/>for collection and time"]
           Search --> Found{"Did the catalog find<br/>every requested collection?"}
           Found -- no --> Reject["Reject the request<br/>as an invalid collection"]
       end

       subgraph Choice["3. Choose response type"]
           Found -- yes --> WantsOriginal{"Can the request return<br/>existing catalog files?"}
           WantsOriginal -- "yes: original_files<br/>or atlas shortcut" --> CatalogOriginal["Return catalog download URLs"]
           WantsOriginal -- no --> ChangesData{"Does the operation need<br/>new data to be written?"}
           ChangesData -- "yes: average, regrid,<br/>or dimension change" --> CatalogOperation["Resolve catalog files<br/>for processing"]
           ChangesData -- no --> Aligned{"Does the subset match<br/>whole source files?"}
           Aligned -- yes --> AlignedOriginal["Return only the matching<br/>download URLs"]
           Aligned -- no --> CatalogOperation
       end

       subgraph Run["4. Execute or adapt the result"]
           DirectFiles --> BuildSources["Build dataset sources"]
           PlainOperation --> BuildSources
           CatalogOperation --> BuildSources
           BuildSources --> Open["Detect data format and transport<br/>NetCDF, Zarr, Kerchunk, file, HTTP, S3"]
           Open --> Fixes["Apply internal dataset fixes<br/>when a dataset id is known"]
           Fixes --> Operation["Run subset, average,<br/>regrid, concat, or weighted average"]
           CatalogOriginal --> OriginalResponse["Return original-file response"]
           AlignedOriginal --> OriginalResponse
           Operation --> OutputResponse["Return operation output files"]
       end

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

Dataset Fix Policy
------------------

Dataset fixes are an internal opening policy, not a WPS input switch. Deprecated
``apply_fixes`` inputs are still accepted for compatibility, but they no longer
decide whether fixes run.

The rule is intentionally small:

* catalog-resolved sources carry a dataset ID and may receive project-specific
  fixes while they are opened;
* direct local, URL, S3, Zarr, and Kerchunk sources without a dataset ID are
  opened as-is;
* workflow outputs are treated like direct files unless a future workflow model
  gives them an explicit source identity.

Decadal concat fixes remain an operation-specific rule for now. They are applied
inside concat because they prepare multiple forecast files for concatenation, not
because the generic dataset opener can infer the whole operation context.

Blueprint for Reimplementation
------------------------------

The future director should be a planner, not an operation runner. It should
return one explicit decision value that describes what the caller must do next:

* reject the request with a known error;
* return original files;
* run an operation with the original collection;
* run an operation with catalog-resolved dataset sources.

The planner should keep these responsibilities separate:

* input classification: workflow files versus collection IDs;
* project and catalog resolution;
* original-file eligibility;
* subset-to-file alignment;
* construction of operation sources;
* WPS response and exception adaptation.

The execution side should be boring on purpose. Given a plan, it should either
collect original-file URLs or prepare operation inputs and call the supplied
runner. It should not repeat catalog decisions.

A future type model could make the decision tree easier to read in code:

.. code-block:: python

   RequestDecision = (
       InvalidRequest
       | ReturnOriginalFiles
       | RunWithOriginalCollection
       | RunWithResolvedSources
   )

The important boundary is that catalog planning decides *what should happen*,
while operation execution decides *how to run the selected operation*.
