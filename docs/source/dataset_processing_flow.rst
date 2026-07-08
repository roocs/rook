.. _dataset_processing_flow:

Dataset Processing Flow
=======================

This page documents the request-resolution and operation-execution flow.
``rook.pflow`` is the processing-flow layer: it classifies request sources,
resolves one request decision, and executes that decision.

The current model is split into three questions:

* what kind of request source did we receive?
* should the request return existing files or run an operation?
* how should the chosen operation open and process its inputs?

At A Glance
-----------

.. mermaid::

   flowchart LR
       Request["Request"] --> Source["Source"]
       Source --> Decision["Decision"]
       Decision --> Execution["Execution"]
       Execution --> Response["Response"]

       Request -.-> RequestHint["WPS call<br/>Workflow step"]
       Source -.-> SourceHint["Collection<br/>Direct dataset<br/>Workflow files"]
       Decision -.-> DecisionHint["Return files<br/>Run operation<br/>Reject request"]
       Execution -.-> ExecutionHint["subset<br/>average<br/>regrid<br/>concat"]

       class RequestHint,SourceHint,DecisionHint,ExecutionHint note
       classDef note fill:#fff7d6,stroke:#c58a00,stroke-dasharray: 4 3,color:#3b2a00

Processing Phases
-----------------

The high-level flow is deliberately small. It shows the stable phases that WPS
requests and workflow steps pass through before a response is built.

.. mermaid::

   flowchart TD
       Start(["WPS request or workflow step"])

       Start --> Normalize["Receive and normalize inputs"]
       Normalize --> Source["Identify request source"]
       Source --> Context["Resolve request context"]
       Context --> Decide["Choose response path"]

       Decide --> Original["Return original files"]
       Decide --> Prepare["Prepare operation inputs"]
       Decide --> Invalid["Reject invalid request"]

       Prepare --> FixPolicy["Apply dataset fix policy"]
       FixPolicy --> RunOps["Run operation"]
       RunOps --> AdaptOperation["Adapt operation result"]
       Original --> AdaptOriginal["Adapt original-file result"]
       Invalid --> AdaptError["Adapt error"]

       AdaptOperation --> End(["WPS/workflow response"])
       AdaptOriginal --> End
       AdaptError --> End

       Source -.-> SourceNotes["Catalog collection<br/>Direct dataset<br/>Workflow files"]
       Context -.-> ContextNotes["Project config<br/>Catalog lookup<br/>Dataset source identity"]
       Decide -.-> DecisionNotes["Original files<br/>Operation processing<br/>Invalid request"]
       FixPolicy -.-> FixNotes["Catalog-backed sources may receive fixes<br/>Direct sources open as-is<br/>Workflow outputs stay direct unless identified"]
       RunOps -.-> OperationNotes["subset<br/>average<br/>regrid<br/>concat<br/>weighted average"]

       class SourceNotes,ContextNotes,DecisionNotes,FixNotes,OperationNotes note
       classDef note fill:#fff7d6,stroke:#c58a00,stroke-dasharray: 4 3,color:#3b2a00

Detailed Decision Rules
-----------------------

The detailed flow names the current request sources, decision values, and
operation execution paths. It is more specific than the phase diagram, but it
should still keep branch rules visible rather than hiding them in broad
orchestration terms.

.. mermaid::

   flowchart TD
       Start(["Request arrives"])
       Start --> WPS["WPS process adapter"]
       Start --> Workflow["Workflow step"]

       subgraph WorkflowLayer["Workflow operation vocabulary"]
           Workflow --> Registry["Look up step run value<br/>in WORKFLOW_OPERATIONS"]
           Registry --> PreviousFiles{"Previous step<br/>produced files?"}
           PreviousFiles -- yes --> WorkflowFiles["WorkflowFiles"]
           PreviousFiles -- no --> WorkflowCollection["Collection input"]
       end

       subgraph Resolution["Request source and decision"]
           WPS --> Collection["Collection input"]
           WorkflowCollection --> Collection
           Collection --> Project["Resolve project"]
           Project --> UsesCatalog{"Project uses<br/>Rook catalog?"}
           UsesCatalog -- no --> DirectDataset["DirectDataset"]
           UsesCatalog -- yes --> CatalogCollection["CatalogCollection"]
           CatalogCollection --> Search["Search catalog<br/>with collection and time"]
           Search --> Found{"All requested collections<br/>found?"}
           Found -- no --> Invalid["InvalidRequest<br/>or InvalidCollection"]
           Found -- yes --> ReturnPolicy{"Can return<br/>existing files?"}
           ReturnPolicy -- "original_files<br/>or project policy" --> ReturnOriginal["ReturnOriginalFiles"]
           ReturnPolicy -- no --> Processing{"Operation must<br/>write new data?"}
           Processing -- yes --> RunResolved["RunOperation<br/>with DatasetSource values"]
           Processing -- no --> Aligned{"Subset aligns with<br/>whole source files?"}
           Aligned -- yes --> ReturnOriginal
           Aligned -- no --> RunResolved
           DirectDataset --> RunOriginal["RunOperation<br/>with original collection"]
       end

       subgraph Execution["Execution and response"]
           WorkflowFiles --> WorkflowPrepare["Prepare workflow file inputs<br/>as FileMapper"]
           WorkflowPrepare --> OperationRunner["Operation runner"]
           RunOriginal --> PrepareOriginal["Clean operation inputs"]
           RunResolved --> PrepareResolved["Clean operation inputs<br/>and replace collection"]
           PrepareOriginal --> OperationRunner
           PrepareResolved --> OperationRunner
           OperationRunner --> Consolidate["Consolidate inputs<br/>to DatasetSource"]
           Consolidate --> Open["Detect format and transport<br/>NetCDF, Zarr, Kerchunk, file, HTTP, S3"]
           Open --> Fixes["Apply dataset fixes<br/>only when dataset id is known"]
           Fixes --> Operation["Run subset, average,<br/>regrid, concat, or weighted average"]
           ReturnOriginal --> OriginalResponse["Original-file response"]
           Operation --> OutputResponse["Operation output files"]
       end

Decision Ownership
------------------

WPS process adapters parse WPS inputs, choose the operation runner, and pass the
request to ``execute_resolved_request``. They do not decide catalog behavior
themselves.

``rook.workflow`` parses workflow documents, resolves dependencies between
steps, and looks up each step's ``run`` value in ``WORKFLOW_OPERATIONS``. Outputs
from previous steps enter the operation adapter as ``WorkflowFiles`` and are
prepared as a ``FileMapper`` before running the next operation.

``rook.pflow.resolver.resolve_request_decision`` handles catalog-backed
requests. It classifies inputs as ``CatalogCollection`` or ``DirectDataset``,
validates catalog search results, and chooses a ``ReturnOriginalFiles`` or
``RunOperation`` decision.

``rook.pflow.execution.execute_decision`` adapts the decision into output URIs.
It collects original file URLs when processing is skipped, otherwise it
prepares operation inputs and calls the operation runner.

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

Current Decision Values
-----------------------

The resolver returns one explicit decision value that describes what the caller
must do next:

* reject the request with a known error;
* ``ReturnOriginalFiles``;
* ``RunOperation`` with the original collection;
* ``RunOperation`` with catalog-resolved ``DatasetSource`` values.

The resolver should keep these responsibilities separate:

* input classification: catalog collection versus direct dataset;
* project and catalog resolution;
* original-file eligibility;
* subset-to-file alignment;
* construction of operation sources;
* WPS response and exception adaptation.

The execution side should be boring on purpose. Given a decision, it should
either collect original-file URLs or prepare operation inputs and call the
supplied runner. It should not repeat catalog decisions.

The type vocabulary is intentionally small:

.. code-block:: python

   RequestDecision = (
       InvalidRequest
       | ReturnOriginalFiles
       | RunOperation
   )

The important boundary is that request resolution decides *what should happen*,
while operation execution decides *how to run the selected operation*.
