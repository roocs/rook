# Rook Release TODO

This checklist tracks the production release after `v1.2.3`. The implementation
work for the Woodpecker handoff is complete. The remaining work is packaging,
environment refresh, release verification, tagging, and deployment.

Rook is deployed as a service. It is not published to PyPI. A Rook release is a
versioned commit and Git tag followed by deployment of the service artifacts.

## Completed

- [x] Define the Rook/Woodpecker boundary: Rook decides whether a source is
  eligible for fixes; Woodpecker owns how those fixes are applied.
- [x] Add the generic fix-provider interface and Woodpecker adapter.
- [x] Route catalog-backed dataset fixes through the configured provider while
  leaving direct local, URL, S3, Zarr, and Kerchunk inputs unchanged.
- [x] Preserve CMIP6-decadal concat preparation through the provider
  `prepare(...)` phase.
- [x] Make Woodpecker the default backend in the packaged and sample
  configuration.
- [x] Retain the legacy provider as an explicit configuration-selected rollback
  option.
- [x] Remove the temporary WPS-level fix-provider override.
- [x] Run smoke tests with one configuration-selected provider instead of
  parametrizing the suite over both providers.
- [x] Keep focused legacy compatibility tests without duplicating the full
  Woodpecker test suite.
- [x] Add focused synthetic Woodpecker coverage for ATLAS, CMIP6-decadal, and
  concat behavior.
- [x] Make mini-ESGF data opt-in for tests that require realistic catalog paths,
  public URLs, or WPS integration fixtures.
- [x] Document the Woodpecker default and legacy rollback configuration.
- [x] Remove Rook's obsolete PyPI/TestPyPI workflows, badge, upload target, and
  publishing dependency.
- [x] Document the manual release-tag flow: merge the version commit first, then
  tag the exact commit on `main`.

## Remaining Release Work

Complete these tasks in order.

### 1. Publish Woodpecker packages

These tasks belong to the Woodpecker repository and must be complete before
Rook stops using Git dependencies.

- [ ] Publish the core distribution as `roocs-woodpecker`. Keep the Python
  import package and command named `woodpecker`.
- [ ] Publish a new Woodpecker version rather than changing the existing
  `v0.7.0` tag, whose metadata still uses the occupied `woodpecker`
  distribution name.
- [ ] Update and publish `woodpecker-atlas-plugin` and
  `woodpecker-cmip6-decadal-plugin` with dependencies on
  `roocs-woodpecker`, not the unrelated `woodpecker` distribution.
- [ ] In a clean environment, install the three distributions from PyPI and
  confirm that `woodpecker`, `woodpecker_atlas_plugin`, and
  `woodpecker_cmip6_decadal_plugin` import successfully.
- [ ] Confirm that Woodpecker discovers the `c3s.atlas` and
  `c3s.cmip6_decadal` recipes from the installed plugins.

### 2. Switch Rook to released Woodpecker packages

- [ ] Replace the three Git URL requirements in `pyproject.toml` with bounded
  released-package requirements for `roocs-woodpecker`,
  `woodpecker-atlas-plugin`, and `woodpecker-cmip6-decadal-plugin`.
- [ ] Replace or remove the matching Git URL entries in
  `requirements_upstream.txt` so it no longer overrides the release packages.
- [ ] Add the released Woodpecker packages to the pip section of
  `environment.yml`. This is required because the production Docker image
  installs Rook with `pip install . --no-deps`.
- [ ] Regenerate `conda-lock.yml`, `linux-64.spec`, and the `spec-file.txt`
  alias with `make conda-spec` on Linux.
- [ ] Recreate the `rook` Conda environment from the refreshed definition and
  confirm `python -m pip check` passes. Remove stale `0.6.x` Woodpecker plugins
  from local or cached environments before interpreting failures.
- [ ] Build the Docker image and confirm all three Woodpecker distributions and
  import packages are present in the image.

### 3. Run the release gate

- [ ] Remove stale generated Sphinx API entries for modules moved under
  `rook.fixes.providers`, `rook.fixes.legacy`, and related utility packages so
  the strict documentation build passes without autodoc import warnings.
- [ ] Run pre-commit over the complete repository.
- [ ] Run focused fix-provider, dataset-opening, pflow, operation, ATLAS,
  CMIP6-decadal, and concat tests.
- [ ] Run the default test suite without smoke or online tests on every
  supported Python version through CI.
- [ ] Build the documentation with warnings treated as errors.
- [ ] Build the Rook wheel and source distribution as local release artifacts.
- [ ] Start the production-style Docker image with Woodpecker configured and
  run the smoke suite once.
- [ ] Confirm the health process returns exactly `ROOK_HEALTH_OK`, including the
  configured filesystem sentinel checks used in production.
- [ ] Run one separately configured legacy-backend smoke check if rollback
  compatibility is required for this deployment.
- [ ] Verify that representative ATLAS and CMIP6-decadal requests produce the
  expected fixed datasets through the deployed service.

### 4. Version, tag, and deploy Rook

- [ ] Finalize the changelog entry for the release and record the released
  Woodpecker package versions.
- [ ] Run `bump-my-version` on a release branch to update and commit the Rook
  version metadata. Do not create the Git tag yet.
- [ ] Merge the release commit through the normal review flow and wait for CI
  to pass on `main`.
- [ ] Update local `main` and create an annotated `vX.Y.Z` tag on the exact
  merged commit.
- [ ] Push the single release tag and create the GitHub release if one is used
  for deployment tracking.
- [ ] Deploy the tagged service artifacts to production.
- [ ] Run post-deployment health, smoke, ATLAS, and CMIP6-decadal checks.
- [ ] Record the deployed Rook and Woodpecker versions and retain the documented
  `[fixes] backend = legacy` rollback procedure.

## Release Guardrails

- Preserve the public WPS process interface, including deprecated compatibility
  inputs still used by CDS clients.
- Apply project-specific fixes only when the dataset source has sufficient
  catalog identity.
- Keep direct local, URL, S3, Zarr, and Kerchunk inputs opening as-is.
- Preserve workflow chaining, public output URLs, naming, splitting,
  provenance, and error-response behavior.
- Run project commands through the explicit `rook` Conda environment.
- Do not make broader mini-ESGF cleanup or object-storage feature work a blocker
  unless a concrete release regression requires it.

## Deferred Work

- Revisit the provider lifecycle after production experience with Woodpecker,
  especially the CMIP6-decadal `prepare(...)` phase.
- Continue cleanup of operators, `rook.pflow`, `workflow.py`, dashboard, usage,
  and WPS process modules.
- Replace hard-coded smoke workflow documents with small Python builders.
- Extend the health process only after deeper operational checks have a stable
  contract.
- Add live S3 integration coverage and future S3/Zarr output support.
- Continue mini-ESGF replacement work after the production release.
