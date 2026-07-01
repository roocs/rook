# Rook Cleanup TODO

This document describes the cleanup phase following the initial Kerchunk, S3,
and Zarr support released in Rook 1.2.0. The aim is to make the existing code
smaller, clearer, and easier to change without adding new storage features.

Keep the work in small, reviewable pull requests. Preserve WPS behavior unless
a change is explicitly documented and tested.

## Goals

- remove dead code, obsolete branches, and misleading options;
- give operators a clear namespace and a small, useful shared abstraction;
- remove duplicated execution paths and unnecessary wrappers;
- separate request planning from operation execution;
- simplify or replace the director;
- document the final dataset-processing flow once it has settled.

## 1. Characterize the Current Execution Paths

Before changing structure, add or improve tests around the decisions that are
currently spread across the WPS processes, `rook.operator`, `rook.director`, and
`rook.utils.ops`.

Cover at least:

- a catalog collection resolved to files and processed by an operator;
- a direct filesystem collection processed without catalog lookup;
- returning original catalog file URLs when a subset aligns with whole files;
- generating a subset when the request does not align with whole files;
- operators that must always process data rather than return original files;
- a later workflow step receiving files produced by an earlier step;
- errors for unknown collections.

Tests should describe observable behavior, not preserve incidental class or
module structure. They will provide room to simplify the implementation.

## 2. Deprecate the `apply_fixes` WPS Parameter

Rook already decides internally whether a dataset fix is required. Callers
should not control that decision.

- keep `apply_fixes` in the WPS process inputs for compatibility;
- mark it as deprecated in each WPS parameter description and user-facing
  documentation;
- continue accepting both true and false values, but do not use the supplied
  value to select internal behavior;
- make fix application an internal dataset-opening or preparation decision;
- remove `apply_fixes` plumbing from workflows, operators, utility functions,
  provenance filtering, and internal APIs where it no longer has meaning;
- remove disabled fix-selection branches in the director after their behavior
  has been replaced;
- add tests proving that the deprecated input is accepted and does not alter
  results.

Use one internal policy for fixes. Catalog-backed datasets may carry the
dataset ID needed to select a fix; direct paths should not accidentally receive
project-specific fixes.

## 3. Clean Up the Operator Layer

There are currently overlapping operator concepts in `rook.operator` and
`rook.utils.ops`, with operation-specific runners elsewhere in `rook.utils`.
Give this code one obvious home and one vocabulary.

A likely target namespace is `rook.operations`, containing:

```text
rook/operations/
    base.py
    subset.py
    average.py
    concat.py
    regrid.py
    execution.py
```

The exact layout should follow the responsibilities discovered during the
cleanup; do not preserve a package structure merely for symmetry.

- inventory the public and internal imports before moving modules;
- decide whether `Operator` and `Operation` represent genuinely different
  concepts; merge or rename them if they do not;
- define a small base class only for behavior shared by every operation;
- prefer explicit functions and composition for optional behavior;
- replace `_get_runner()` subclasses that only return a function with a simpler
  registration or direct callable when appropriate;
- centralize output-directory creation and result handling;
- remove pass-through wrappers and duplicated parameter normalization;
- keep clisops calls visible and easy to trace;
- use names that distinguish WPS process adapters from data operations.

Avoid designing a large framework. The base classes should remove repetition,
not hide control flow.

## 4. Reconsider the Director

The director currently performs several jobs at once:

- catalog lookup and validation;
- deciding whether original files can be returned;
- checking subset-to-file alignment;
- rewriting collections for processing;
- invoking an operation runner;
- translating exceptions and packaging results.

First make these decisions explicit, then decide whether the `Director` class
still earns its place. A useful intermediate design may be a small request plan
with an explicit outcome, for example:

```python
plan = plan_request(collection, parameters)

if plan.returns_original_files:
    return plan.original_file_urls

return run_operation(plan.dataset_sources, parameters)
```

Possible focused components are:

- catalog collection resolution;
- original-file eligibility and subset alignment;
- operation execution;
- WPS exception and response adaptation.

The result should avoid mutable input dictionaries as hidden communication.
Decision results should be explicit values with clear types. If the director
becomes only a thin wrapper after extraction, remove it.

### Note for Future Us

After the first `planning.py` extraction, the split between `Director` and
request planning is intentionally intermediate. It is better than the previous
all-in-one director, but it is not the final design.

When returning to this area, first ask whether `Director` still adds value or
has become a thin compatibility wrapper. Also revisit whether request plans
should carry prepared dataset sources directly, and whether WPS
exception/response adaptation can be separated cleanly from operation
execution.

## 5. Remove Dead and Misleading Code

Do this continuously, but keep behavior changes separate from mechanical moves.

- remove unreachable code after unconditional returns;
- remove commented-out implementations and stale TODO comments;
- find parameters, attributes, helpers, compatibility modules, and imports with
  no callers;
- remove old module names once all internal imports have moved;
- replace broad exception handling where a narrower boundary is known;
- remove mutation and defensive copying that no longer serve a purpose;
- simplify boolean branches and duplicated conditionals;
- update tests that only exercise deleted implementation details.

For each candidate, use repository-wide searches and test coverage before
removal. Code that supports a real WPS input or response remains public even if
Rook's Python modules have no external users.

## 6. Document the Dataset-Processing Flow

Add the architecture documentation only after the operator and director cleanup
has stabilized, so the diagram describes the code rather than an aspiration.

The documentation should include a Mermaid flowchart showing:

- entry through a WPS process;
- catalog dataset IDs versus direct filesystem, URL, S3, Zarr, and Kerchunk
  inputs;
- catalog lookup and file resolution;
- the decision to return original files or perform processing;
- construction of `DatasetSource` values;
- format detection and transport configuration;
- internal dataset fixes where applicable;
- subset or other operator execution;
- output file and original-file responses.

Keep the diagram at the architectural level. Link important nodes to short
sections explaining ownership and decision rules rather than embedding every
special case in the chart.

## Suggested Pull Request Order

1. Characterization tests and an inventory of operator/director responsibilities.
2. Deprecate the WPS `apply_fixes` input and remove its internal control flow.
3. Introduce the operator namespace and consolidate common execution behavior.
4. Migrate individual operators in small groups, removing old wrappers as they
   become unused.
5. Extract catalog resolution and original-file planning from the director.
6. Remove or reduce the director and clean up the resulting dead code.
7. Add the Mermaid architecture documentation and a final terminology pass.

## Guardrails

Every cleanup pull request should demonstrate that:

- the WPS process interface remains compatible, including deprecated inputs;
- ordinary local and catalog-resolved NetCDF processing is unchanged;
- Kerchunk, Zarr, and S3 inputs continue through the common dataset-opening API;
- direct paths do not require catalog configuration;
- original-file responses still contain public download URLs, not internal
  processing paths;
- multi-step workflows can consume files created by earlier steps;
- output naming, splitting, provenance, and error responses remain stable unless
  a deliberate change is documented.

Run the focused tests while iterating, followed by the full test suite and all
repository hooks before each pull request.

## Deferred Features

These remain outside this cleanup phase:

- live S3 integration tests requiring external test data or credentials;
- writing operation output directly to S3 or Zarr;
- combining multiple Zarr stores or selecting Zarr groups through WPS inputs;
- supporting additional object-store protocols;
- replacing established clisops dataset-opening behavior;
- redesigning all Rook configuration at once.
