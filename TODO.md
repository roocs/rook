# Rook Cleanup TODO

This document tracks the cleanup phase after the `v1.2.3` release.

The previous phase renamed the internal request-processing layer from
`rook.director` to `rook.pflow`, clarified the request-decision vocabulary, and
documented the dataset-processing flow. The next phase should keep that shape
stable while integrating the Woodpecker fixes library.

Keep the work in small, reviewable pull requests. Preserve WPS behavior unless
a change is explicit, documented, and covered by tests.

## Current Phase Goal

Integrate the Woodpecker fixes library so dataset/project fixes are no longer
owned by Rook-specific utility code. The goal is not a broad operator rewrite.
It is to move fix responsibility to Woodpecker while keeping Rook's source
classification, request decisions, operation execution, and WPS response
behavior stable.

Implementation details are tracked below and should be pruned as the
Woodpecker integration PRs land.

## Phase Goals

- identify the current Rook fix entry points and the source identity each one
  receives;
- map Rook's dataset/project fix behavior to Woodpecker concepts;
- keep the pflow dataset-fix policy explicit while delegating the actual fixes;
- make dataset fixes part of the normal data/processing flow instead of
  operation-specific hooks added only where they are needed;
- preserve concat-specific CMIP6 decadal behavior until it can be represented
  cleanly through Woodpecker;
- keep direct local, URL, S3, Zarr, Kerchunk, catalog-backed, and workflow-file
  inputs behaviorally stable;
- remove obsolete Rook fix helpers only after Woodpecker-backed behavior is
  covered by focused tests;
- document the new fix boundary clearly enough that future operator and pflow
  cleanup can continue without another vocabulary pass.

## Fix Boundary To Clarify

These names should stay boring and predictable:

- dataset source identity: the project/dataset information needed to decide
  whether fixes may be applied;
- dataset fix policy: Rook-side policy that decides when a source is eligible
  for fixes;
- fix provider: Woodpecker-backed code that applies the actual dataset/project
  fixes;
- operation-specific preparation: fixes or preparation that belong to a
  specific operation, for example concat's current decadal preparation;
- direct source: local/remote user input that should open as-is unless it has
  explicit source identity.

Rook should decide *whether* a dataset source is eligible for fixes. Woodpecker
should own *how* those fixes are applied.

## Suggested Pull Request Order

1. Document the intended Woodpecker integration boundary in this TODO and, if
   useful, in the dataset-processing flow docs.
2. Add Woodpecker as a dependency and introduce a tiny Rook adapter around it.
3. Route catalog-backed dataset fixes through the adapter without changing WPS
   inputs or response behavior.
4. Add focused tests for catalog-backed NetCDF fixes, direct inputs without
   fixes, workflow-file inputs, and concat decadal behavior.
5. Remove obsolete Rook-side fix helpers once the Woodpecker-backed path is
   covered.
6. Refresh docs and changelog.
7. Run focused pflow/operator tests, docs, the default non-smoke suite, and
   smoke tests before release.

## Phase Checklist

Use this as the running progress log for the phase. Tick a box only after the
corresponding PR has landed.

- [ ] Woodpecker integration boundary is written down.
- [ ] Woodpecker dependency is added.
- [ ] Rook has a small Woodpecker adapter or provider.
  Note: keep the provider interface generic. The main provider method should be
  `apply(ds, context=...)`, with optional `prepare(...)` and `finalise(...)`
  hooks for operation lifecycle needs. Avoid adding new provider methods named
  after specific projects, activities, or fixes unless there is no generic
  lifecycle boundary for the behavior. The usefulness of the lifecycle phases
  should be revisited after decadal data providers have gained practical
  experience with Woodpecker. Do not remove or rename the phases only from an
  interface-design concern while that feedback is still being collected.
- [ ] Catalog-backed dataset fixes use Woodpecker.
- [ ] Direct local, URL, S3, Zarr, and Kerchunk inputs still open as-is.
- [ ] Workflow-file inputs still feed later workflow steps.
- [ ] Concat decadal behavior is preserved or explicitly moved to Woodpecker.
  Note: concat still has a special CMIP6-decadal pre-concat calendar
  preparation step for proleptic Gregorian inputs. It is now hidden behind the
  generic `prepare(...)` hook. The Woodpecker provider uses the direct
  `cmip6_decadal.calendar_normalization` fix for this step; the legacy provider
  still delegates to the old Rook helper. Decide whether this remains an
  operation-specific Rook preparation hook or becomes a more explicit
  Woodpecker recipe/phase.
- [ ] Keep refining config-driven fix provider selection. Rook now chooses the
  default provider internally from `roocs.ini` (`[fixes] backend = ...`) and
  CMIP6-decadal smoke/parity tests can temporarily override that default through
  the `fix_provider` WPS input on the `concat` process. The next cleanup step is
  deciding when the legacy backend, the temporary WPS override, and any
  remaining compatibility handling can be removed.
- [ ] Clean up the parity-test setup. The current checks are useful while
  validating the Woodpecker integration, but the setup should become simpler
  and more direct so we do not keep complicated integration scaffolding around.
  Note: focused fix/provider tests now use Woodpecker synthetic data, and
  mini-esgf-data is opt-in for tests that need realistic catalog/path behavior.
  Keep looking for remaining parity scaffolding that can be retired once the
  Woodpecker-backed path has settled.
- [ ] Obsolete Rook fix helpers are removed or explicitly justified.
- [ ] Focused pflow/operator tests cover the new fix boundary.
- [ ] Documentation and changelog describe the Woodpecker handoff.
- [ ] Smoke tests pass after the integration.

## Guardrails

Every pull request should demonstrate that:

- code and documentation stay clean, simple, and direct;
- abstractions are added only when they make the processing flow easier to
  read;
- the WPS process interface remains compatible, including existing inputs used
  by CDS calls; avoid changing public WPS inputs unless there is an explicit
  migration plan because CDS API changes have a longer adaptation cycle;
- direct local, URL, S3, Zarr, and Kerchunk inputs still work;
- catalog-backed NetCDF processing is unchanged except for the delegated fix
  implementation;
- original-file responses still contain public download URLs;
- workflow outputs can feed later workflow steps;
- dataset fixes are applied only when the source identity supports them;
- output naming, splitting, provenance, and error responses remain stable unless
  a deliberate change is documented.

For this phase and future cleanup tasks, always run project commands through the
`rook` conda environment. Do not rely on the active shell environment; use an
explicit command such as `conda run -n rook pytest ...` so verification uses the
same dependencies as the project setup.

Run focused tests while iterating, followed by lint, docs, and the default
non-smoke test suite before each pull request.

## Future Work

These are intentionally outside the first Woodpecker integration step, but they
should stay visible:

- do another iteration on operators after the fix boundary is clearer;
- do another iteration on `rook.pflow` after Woodpecker integration settles;
- revisit the processing flow once Woodpecker users, especially decadal data
  providers, have practical experience with the current provider interface.
  The target shape is an explicit flow with source resolution, source identity,
  opening, preparation, dataset/project fixes, operation execution, and output
  finalization as named stages, rather than fixes being squeezed into
  individual operators;
- review and clean up the `workflow.py` component;
- clean up smoke tests so workflows and process inputs are built with small
  Python helpers instead of large hard-coded JSON documents, making provider
  and parameter variants easier to tweak;
- refactor the dashboard process;
- refactor the usage process;
- add a new process for health checks;
- clean up all WPS process modules in general.

## Synthetic Test Data

Woodpecker already provides synthetic test data builders such as
`woodpecker.testing.make_cmip6_decadal`, `make_atlas`, `make_cmip6`, `make_cmip7`,
and `make_cordex`. Use these for focused fix/provider tests while keeping
mini-esgf-data for integration coverage that needs realistic catalog paths,
public URL behavior, WPS catalog configuration, or path-resolution behavior.

Status: the first synthetic-data cleanup PR is done. It made mini-esgf-data
opt-in, added focused synthetic coverage for decadal and atlas fixes, added
synthetic concat coverage with temporary NetCDF files, and added a regression
check that concat finalization writes to the configured output directory.

Work in small steps:

1. [x] Make mini-esgf-data opt-in for tests that actually need it.
   `load_test_data` and the mini-ESGF roocs config fixture are no longer
   session-autouse; tests that need them use the `mini_esgf_data` marker and
   `load_test_data` fixture explicitly.
2. [x] Keep mini-esgf-data coverage for WPS, catalog lookup, path resolution,
   metalink/public URL behavior, and other integration checks that need the
   realistic file layout. These tests are marked with `mini_esgf_data`.
3. [x] Add or migrate focused fix tests to synthetic Woodpecker data, especially
   decadal calendar preparation, decadal apply behavior, atlas fixes, and
   provider routing.
4. [x] Add synthetic concat coverage using temporary NetCDF files so the
   per-file `prepare` step, grouped time concat, and dataset-id-aware `apply`
   step are tested without depending on mini-esgf-data.

## Deferred Features

These remain outside this cleanup phase:

- live S3 integration tests requiring external test data or credentials;
- writing operation output directly to S3 or Zarr;
- combining multiple Zarr stores or selecting Zarr groups through WPS inputs;
- supporting additional object-store protocols;
- replacing mini-esgf-data;
- redesigning all Rook configuration at once.
