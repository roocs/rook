# Rook Cleanup TODO

This document tracks the next cleanup phase after the `v1.2.1` release. The
previous phase removed compatibility shims, moved operations into
`rook.operations`, reduced the old director, cleaned dead code, and added the
dataset-processing decision diagram.

The next phase should make the decision model itself simpler. The current
diagram is useful because it shows the truth, but the truth is still too hard
to read.

Some decision rules are unavoidably hard-coded for now. The goal of this phase
is not to pretend they can all disappear; it is to make each rule named,
localized, tested, and documented so the surrounding flow stays human-readable.

Keep the work in small, reviewable pull requests. Preserve WPS behavior unless
a change is explicit, documented, and covered by tests.

## Goals

- reimplement the "director" as a readable request planner;
- make workflow inputs an explicit case, not a hidden bypass;
- represent request outcomes as clear values: processed files, original files,
  or failure;
- keep dataset fixes as an internal data-opening/preparation policy;
- simplify operation execution around clisops now that daops is integrated;
- make the workflow code easier to read and less coupled to WPS details;
- update docs and diagrams so they explain the model, not the mess.

## Current Logic Quirks to Untangle

These are the places that make the current decision tree hard to understand.
Use this list to guide small PRs and to avoid accidentally preserving accidental
structure.

- Workflow outputs are detected in `Operator.call()` with `is_file_list()`,
  while catalog planning happens in `rook.director`. That means the "director"
  does not really own the whole request decision.
- The code decides that an operation must process data by checking parameter
  names such as `dims`, `freq`, and `grid`. This hides operation intent in
  request-shape details.
- Returning original files mixes several policies: explicit `original_files`,
  subset-to-file alignment, and special project behavior such as
  `c3s-ipcc-atlas`.
- The result shape is implicit. Internally we return operation output files,
  original file URLs, or failures, but this is not modeled as a small set of
  named outcomes.
- `FileMapper` instances are used as prepared dataset sources and receive
  `dataset_id` dynamically. That makes catalog-resolved inputs harder to see
  and type.
- Dataset fixes are mostly internal now, but the policy is still scattered:
  generic dataset opening applies catalog-specific fixes, concat has decadal
  fix handling, and the director still carries an atlas-related TODO.
- Broad exception translation happens at multiple boundaries. It is not always
  obvious where domain errors end and WPS adaptation begins.
- Mutable input dictionaries still carry too much meaning. Cleaning,
  normalizing, and replacing `collection` should happen at explicit boundaries.
- WPS process adapters, workflow execution, request planning, operation running,
  and response adaptation still know too much about each other.
- Hard-coded project, parameter, and operation checks are mixed into the control
  flow. Even when a rule must stay, it should live behind a named predicate or
  policy object that says why the decision exists.

## 1. Characterize the Request Decision Model

Before reimplementation, write or tighten tests that describe behavior in terms
of request outcomes rather than current modules.

Cover at least:

- catalog collection resolved to processing files;
- direct local NetCDF input processed without catalog lookup;
- direct URL, S3, Zarr, and Kerchunk inputs that bypass catalog lookup;
- workflow step receiving files produced by an earlier step;
- explicit `original_files=True`;
- subset request aligned with whole files and returned as original URLs;
- subset request not aligned with whole files and processed;
- operations that must always write new data;
- unknown catalog collection failures;
- catalog-backed datasets receiving fixes through dataset IDs;
- direct paths not receiving project-specific fixes.

Use the existing diagram in `docs/source/dataset_processing_flow.rst` as the
test matrix, but let the tests name the behavior we want, not the functions we
currently have.

## 2. Define Explicit Request Outcomes

Create a small vocabulary for the request planner. A useful shape may be:

```python
RequestDecision = (
    InvalidRequest
    | ReturnOriginalFiles
    | RunOperation
)
```

`RunOperation` can then carry either the original request collection or prepared
dataset sources. Avoid making "catalog-backed" and "workflow-backed" hidden
side effects.

The public result should also be boring and explicit:

- processed files;
- original files;
- failure.

Keep WPS response objects out of the planner. The planner should decide what
should happen; the adapter should decide how to express that decision as a WPS
response or error.

## 3. Make Workflow Inputs Explicit

Workflow handling currently enters through the same operation adapter as WPS
requests, then bypasses the director when the collection is already a file
list. Make that an explicit request source.

Possible request sources:

- `CatalogCollection`;
- `DirectDataset`;
- `WorkflowFiles`.

The important point is that workflow files should not look like a surprising
special case inside `Operator.call()`. They should be planned or adapted through
a named path, with tests proving multi-step workflows still consume previous
step outputs.

## 4. Reimplement the Director as a Planner

The new director should be small enough to read without the diagram.

Candidate responsibilities:

- classify the request source;
- resolve project/catalog metadata only when needed;
- validate catalog matches;
- decide original-file eligibility;
- decide whether processing is required;
- prepare operation sources when processing catalog data;
- return a typed decision.

Hard-coded rules may remain where they describe current behavior, but they
should be isolated behind readable names such as
`requires_processing(operation, inputs)`,
`may_return_original_files(project, operation, inputs)`, or
`requires_catalog_fix(source)`. Avoid letting low-level checks such as
parameter names or project IDs dominate the main planning flow.

Non-responsibilities:

- running clisops operations;
- creating output directories;
- mutating WPS input dictionaries;
- formatting WPS responses;
- applying dataset fixes directly.

When the new planner exists, remove old compatibility names such as
`wrap_director` if process imports can be updated clearly.

## 5. Keep Fixes Internal and Central

Use one explicit policy for dataset fixes:

- catalog-backed sources may carry a dataset ID and receive fixes;
- direct sources without a dataset ID should not receive project-specific fixes;
- workflow outputs should not accidentally inherit catalog fixes unless they
  carry an explicit source identity;
- operation-specific fixes, especially decadal concat handling, should be
  reviewed and either moved into the same preparation layer or documented as a
  deliberate operation rule.

Remove stale atlas/director TODO branches once the policy is expressed in code
and covered by tests.

## 6. Revisit Operators from a Clean clisops Baseline

Daops is now integrated, so the next operator cleanup can start from what Rook
actually needs on top of clisops.

Questions to answer:

- Which operation wrappers are still necessary?
- Which parameter normalization belongs in WPS adapters, and which belongs in
  operation code?
- Can output-directory creation and output naming be made shared but visible?
- Can the `Operator` subclasses that only return a runner disappear?
- Can weighted average and concat use the same operation vocabulary as subset,
  average, and regrid?
- Can operations accept prepared dataset sources directly, without `FileMapper`
  as hidden communication?

Prefer plain functions and small data values over another framework. Keep
clisops calls visible.

## 7. Review Workflow Execution

After the request planner and operation vocabulary are clearer, revisit
`rook.workflow`.

Focus on:

- parsing workflow documents into explicit steps;
- passing previous step outputs as `WorkflowFiles`;
- avoiding duplicated per-operation branches;
- keeping provenance updates close to step execution but out of request
  planning;
- preserving current WPS orchestrate behavior.

## 8. Update the Documentation

The current Mermaid diagram is a map of the old world. As the code gets simpler,
revise it until it can explain the new model without causing pain.

Docs should include:

- request source types;
- planner outcomes;
- original-file versus processed-file responses;
- where fixes are applied;
- how workflow steps pass data;
- which layer owns WPS adaptation.

## Suggested Pull Request Order

1. Add characterization tests for request outcomes and workflow file inputs.
2. Introduce request source and decision types without changing behavior.
3. Move workflow file handling out of the hidden `Operator.call()` branch.
4. Reimplement catalog/original-file planning using the new decision model.
5. Replace `wrap_director` process usage with the new planner/adapter names.
6. Centralize and document dataset-fix policy.
7. Simplify operation adapters around clisops and remove runner-only classes.
8. Clean up `rook.workflow` after the operation path is simpler.
9. Refresh the Mermaid diagram and architecture docs.

## Follow-Up Notes

- Keep the immediate mini ESGF test-data fix inside Rook and leave clisops
  untouched. The current fixture should use the existing clisops/Pooch `stratus`
  helper, but the Rook-side selection of required files should be made a little
  nicer: easier to read, named by test-data purpose, and documented as a
  temporary bridge until mini-esgf-data is replaced in a later phase.

## Phase Checklist

Use this as the running progress log for the phase. Tick a box only after the
corresponding PR has landed.

- [x] Request outcome characterization tests are in place.
- [x] Workflow file inputs are covered by tests and named explicitly.
- [x] Request source types are introduced.
- [x] Planner decision types are introduced.
- [x] Hard-coded decision rules are isolated behind named predicates or
  policies.
- [x] Catalog and original-file planning use the new decision model.
- [x] `wrap_director` has been replaced or intentionally kept with a documented
  reason.
- [ ] Dataset-fix policy is centralized, tested, and documented.
- [ ] Operation adapters have been simplified around clisops.
- [ ] Runner-only `Operator` classes are removed or justified.
- [ ] `rook.workflow` uses the clearer operation/request vocabulary.
- [ ] Mermaid architecture docs describe the new model.

## Guardrails

Every pull request should demonstrate that:

- the WPS process interface remains compatible;
- deprecated inputs such as `apply_fixes` are still accepted;
- direct local, URL, S3, Zarr, and Kerchunk inputs still work;
- catalog-backed NetCDF processing is unchanged;
- original-file responses still contain public download URLs;
- workflow outputs can feed later workflow steps;
- dataset fixes are applied only when the source identity supports them;
- output naming, splitting, provenance, and error responses remain stable unless
  a deliberate change is documented.

Run focused tests while iterating, followed by lint, docs, and the default
non-smoke test suite before each pull request.

## Deferred Features

These remain outside this cleanup phase:

- live S3 integration tests requiring external test data or credentials;
- writing operation output directly to S3 or Zarr;
- combining multiple Zarr stores or selecting Zarr groups through WPS inputs;
- supporting additional object-store protocols;
- redesigning all Rook configuration at once.
