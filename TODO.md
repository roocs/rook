# Rook Release and Cleanup TODO

This document tracks the cleanup and release-preparation phase after the
`v1.2.3` release.

The previous phases renamed the internal request-processing layer from
`rook.director` to `rook.pflow` and integrated the Woodpecker fixes library.
The next phase should keep that shape stable while preparing a production-ready
release.

Keep the work in small, reviewable pull requests. Preserve WPS behavior unless
a change is explicit, documented, and covered by tests.

## Current Phase Goal

Prepare a new Rook release that is suitable for production deployment. The
Woodpecker integration is far enough along for this release; the remaining work
should simplify provider selection, remove unnecessary parity-test complexity,
complete release verification, and document the deployment-ready state.

Woodpecker should become the default fix provider. Keep the legacy provider as
a configuration-selected fallback, including for targeted smoke-test runs, but
do not run both providers in parallel through every smoke test. A smoke-test run
should exercise the single provider selected by configuration. The temporary
WPS-level provider override should be removed when the configuration-driven
tests cover the required cases.

Further mini-ESGF/mini-climate-data work is not a blocker for this release. The
focused synthetic coverage already added is sufficient for the current phase;
broader test-data improvements will continue later.

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

1. Make Woodpecker the configured default fix provider while retaining the
   legacy provider as an explicit configuration fallback.
2. Simplify provider plumbing and tests so production and smoke tests use one
   configuration-selected provider per run. Remove provider parametrization and
   the temporary WPS override where they are no longer needed.
3. Keep a small targeted legacy-provider test set and support an optional smoke
   run with the legacy backend selected in configuration.
4. Remove obsolete Rook fix helpers only where the Woodpecker-backed behavior
   is already covered; explicitly retain any compatibility code still needed
   for the legacy fallback.
5. Refresh deployment configuration, documentation, and changelog for the new
   default and fallback behavior.
6. Run focused pflow/operator tests, lint, docs, the default non-smoke suite,
   and one Woodpecker-configured smoke-test run. Run the legacy smoke path as a
   separate compatibility check when required.
7. Prepare and publish the release, then deploy it to production.

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
- [ ] Make Woodpecker the default backend in `roocs.ini` and keep `legacy` as an
  explicit configuration option.
- [ ] Remove the temporary `fix_provider` WPS override once smoke and focused
  tests can select the backend entirely through configuration.
- [ ] Simplify the parity-test setup. Do not parametrize the smoke suite over
  both providers. Run the suite once with its configured provider, using
  Woodpecker for the release gate and a separate legacy-configured run only
  when compatibility needs to be checked.
- [ ] Keep a focused legacy-provider unit/integration test set without
  duplicating the complete Woodpecker test suite.
- [ ] Obsolete Rook fix helpers are removed or explicitly justified.
- [ ] Focused pflow/operator tests cover the new fix boundary.
- [ ] Documentation and changelog describe the Woodpecker handoff.
- [ ] Smoke tests pass after the integration.
- [ ] Production configuration uses Woodpecker and has a documented legacy
  rollback switch.
- [ ] The release is built, published, and ready for production deployment.

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

These are intentionally outside the immediate production-release work, but
they should stay visible:

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
- define and implement a health-check process after its operational contract,
  checks, and response format have been agreed; this is not a blocker for the
  immediate production release;
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

Pause further mini-ESGF/mini-climate-data cleanup until after the production
release. Do not expand this into a release blocker unless a concrete regression
cannot be covered with the existing focused synthetic data or required
integration fixtures.

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
