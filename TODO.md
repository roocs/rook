# Rook TODO

Only unfinished or deliberately deferred work belongs here. Completed work is
documented in `CHANGELOG.rst`.

## Urgent memory follow-ups

- [ ] Patch clisops so its multi-file dataset opener explicitly uses Xarray's
  new combine defaults (in particular ``data_vars=None``), then remove Rook's
  temporary ``use_new_combine_kwarg_defaults`` compatibility context. The old
  ``data_vars="all"`` behavior can broadcast static CORDEX grid and vertex
  variables across every timestep and cause multi-gigabyte allocations.
- [ ] Measure subset peak RSS with representative high-resolution CORDEX and
  CMIP6 datasets under a 4 GB cgroup limit (production currently allows 6 GB).
  Validate and tune the byte-based planner's 2x writer amplification estimate.
- [ ] **Evaluate the clisops Dask chunk-memory limit.** Benchmark representative
  Rook subset and concat requests with different ``chunk_memory_limit`` values
  (for example 128, 256, and 512 MiB). Compare runtime and peak Slurm RSS to
  identify a performant default that retains sufficient memory headroom.
- [ ] **Add optional Dask performance diagnostics.** Add opt-in diagnostics for
  Rook operations that capture task scheduling, memory usage, spilling, and
  execution time, preferably as a Dask ``performance_report`` attached to the
  request output or logs. Keep diagnostics disabled by default with
  configurable storage and retention.
- [ ] Add the multi-file static-grid regression case to clisops when upstreaming
  the opener fix, including ``lat_vertices`` and ``lon_vertices`` variables.

## Operator performance

Establish representative runtime and I/O baselines before changing execution.
Long daily and hourly requests, especially CORDEX, CMIP6, and CMIP6-decadal,
currently take up to an hour or more. Spatial subsetting often reduces this to a
few minutes, which suggests that source reads and NetCDF writes are important
parts of the bottleneck.

- [ ] Profile representative long-range Atlas, CORDEX daily/hourly, CMIP6
  daily/hourly, and CMIP6-decadal requests, both with and without an area. Record
  wall time per phase and batch, bytes read and written, storage throughput and
  wait, CPU utilization, peak RSS, Dask task time, and output merging time.
- [ ] Add per-phase timing around catalog resolution, source opening, fixes,
  selection, concat, writing, and batch merging so production logs identify the
  dominant phase without enabling a full diagnostic report.
- [ ] Benchmark sequential batches against two concurrent batches on the
  production storage path. Include subset and decadal concat, area-constrained
  and unconstrained requests, and daily and hourly data; verify that concurrency
  improves wall time rather than merely contending for the same storage.
- [ ] If the benchmark is positive, add bounded, configurable batch concurrency
  using a standard-library thread pool. Default conservatively (initially one
  worker), keep output order deterministic, and allow separate deployment
  settings for subset and concat if their resource profiles differ.
- [ ] Make concurrent execution respect a request-level memory budget instead
  of letting every worker independently consume the full batch memory aim.
  Define how worker count and batch size are reduced when their combined
  estimated memory, writer amplification, or open-file count would exceed the
  configured limits.
- [ ] Ensure each concurrent batch has isolated mutable parameters, datasets,
  and output paths. Do not share the current operation object's mutable
  ``params`` between workers; audit clisops, Xarray/Dask configuration, the
  fix provider, NetCDF/HDF5, and file naming for thread safety.
- [ ] Keep final batch merging serialized initially. Add tests for deterministic
  ordering, unique filenames, partial failure and cancellation, cleanup of
  completed/temporary outputs, exception propagation, and datasets being closed
  before considering concurrent writes production-ready.
- [ ] Define an acceptance threshold from the benchmark (wall-time improvement,
  peak/aggregate RSS, I/O saturation, and failure rate) and retain the
  sequential path when two workers do not provide a material benefit.

### Optional processed-artifact cache

Aligned Atlas pass-through requests return their original files and do not need
a cache. The full Atlas collection also exceeds the available cache storage, so
caching is not part of the current Atlas performance solution. It may still be
useful later for demonstrably repetitive, expensive processing results.

- [ ] Reconsider a cache only after production metrics identify repeated
  identical work, a useful expected hit rate, and a working set that fits the
  available storage. Compare the measured benefit with operational complexity
  before selecting a backend.
- [ ] If justified, design a small backend-neutral, disabled-by-default artifact
  cache with canonical versioned keys, atomic publication, bounded capacity and
  eviction, corruption recovery, safe materialization, and observable hit/miss
  and byte statistics. Keep it independent of Atlas-specific control flow.
- [ ] Cover cache correctness and failure behavior with backend contract tests,
  including concurrent misses, source or fix-version changes, incomplete
  entries, eviction, and disk-full fallback. Do not pre-warm the complete Atlas
  collection.

## Job lifecycle controller and explicit project behavior

CMIP6, CORDEX, Atlas, CMIP6-decadal, and the other data projects do not yet
follow one processing policy. Their differences are currently expressed inline
across catalog resolution, processing-flow decisions, operators, fixes, and
configuration. This makes a project exception easy to add but difficult to
discover or explain. Ideally projects should share the same behavior; where
that is not possible, the exception and its reason must be obvious.

Introduce exactly one application-level job controller between the WPS/workflow
adapters and the processing implementation. This controller owns the complete
Rook job lifecycle for every operation and dataset project. Project flavors may
adapt defined parts of its default behavior when necessary, but they do not
create alternative controllers or lifecycles. In the ideal/common case, a
project flavor adds only a name and documentation and inherits all default
behavior. The controller does not replace PyWPS job persistence, the scheduler,
or the individual clisops operations.

### Controller boundary and lifecycle

- [ ] Define one normalized, immutable job request containing the operation,
  inputs, selected dataset project, request/job identifiers, output location,
  and safe diagnostic context. WPS processes and workflow steps should build
  the same request model.
- [ ] Give the controller explicit lifecycle phases: normalize, validate, plan,
  execute, publish results, and finalize/clean up. Represent phase transitions
  and outcomes so logging, status reporting, provenance, and failure mapping do
  not depend on individual process handlers.
- [ ] Enforce one lifecycle implementation for all direct processes, workflow
  operations, and project flavors. A flavor may customize declared hooks, but
  must not bypass, reorder, or reimplement the controller lifecycle.
- [ ] Keep the controller an orchestrator of small components rather than the
  implementation of every operation. Inject or register validators, project
  flavor, resolver/planner, operation runner, result publisher, and cleanup;
  keep subset, regrid, concat, averaging, and workflow execution independently
  testable.
- [ ] Move duplicated control flow from direct WPS handlers and workflow
  operators behind this boundary incrementally. Leave protocol parsing and WPS
  response rendering in thin adapters, and preserve existing public inputs,
  outputs, Metalink documents, and provenance while migrating.
- [ ] Define cancellation, timeout, retry, partial-output, and cleanup behavior
  for every phase. Make finalization idempotent so failed publication or a
  repeated callback cannot leak temporary files or publish a result twice.
- [ ] Emit structured lifecycle events with operation, project-flavor name,
  phase, timing, and stable failure code. Use these events for the future
  service-status view instead of teaching the controller about HTML or
  monitoring backends.

### Generic and project-specific behavior

- [ ] Introduce a named project-flavor strategy selected from normalized
  collection metadata. A flavor is executable behavior, not only configuration:
  it may validate project rules, influence planning and source resolution,
  prepare operation inputs, select fixes/batching, and adapt result publication
  through explicit lifecycle hooks.
- [ ] Provide a well-tested default flavor implementing the common behavior.
  Make the zero-code path the normal one: a conventional project registers its
  name and documentation and inherits the complete default behavior. Only add
  configuration, reusable capabilities, or narrow hook overrides when its data
  model or processing requirements demonstrably differ.
- [ ] Keep operation behavior and project behavior as separate dimensions: the
  controller selects both an operation runner (subset, regrid, concat, and so
  on) and a project flavor. Avoid a growing class for every operation/project
  combination.
- [ ] Initially implement and document flavors for generic CMIP6/CORDEX, Atlas,
  and CMIP6-decadal. Cover the Atlas original-file/fix path and the decadal
  realization/concat lifecycle without overriding the complete controller.
- [ ] Give flavor hooks typed inputs and outputs, documented pre/postconditions,
  and safe defaults. A hook must not silently skip validation, publication,
  cleanup, lifecycle events, or other controller invariants.
- [ ] Fail clearly on an unknown or ambiguous project and record the selected
  flavor plus its rationale in the job plan. Do not infer behavior from
  scattered collection-name checks after planning.
- [ ] Document the generic lifecycle, flavor interface, reusable capabilities,
  configuration options, and a short recipe for adding a conventional project
  versus a project requiring custom behavior.
- [ ] Add controller contract tests that run the same lifecycle suite for
  generic CMIP6/CORDEX jobs, Atlas, CMIP6-decadal, and workflow steps. Assert
  phase ordering, validation timing, selected flavor, failure mapping, cleanup,
  and unchanged public WPS results.

### Project-flavor migration

- [ ] Inventory the behavior of every supported project in one documented
  matrix. Include catalog lookup, original-file eligibility, spatial and
  temporal alignment, required fixes and their phases, concat requirements,
  batching, and relevant configuration. Give the reason for every divergence,
  not only its implementation.
- [ ] Introduce one explicit project-flavor interface and capability model with
  a common default. Select it at the request boundary and pass it through the
  processing flow, instead of comparing project IDs inline in resolvers and
  operators.
- [ ] Keep flavor definitions readable and colocated so a developer can see
  how CMIP6, CORDEX, CICA Atlas, IPCC Atlas, and CMIP6-decadal differ without
  tracing several call paths. Distinguish inherent data-model constraints from
  temporary compatibility or performance workarounds.
- [ ] Make each exceptional behavior carry a short rationale, its configuration
  controls, and focused tests. Add a structural test or lint rule that prevents
  new project-name conditionals outside the flavor layer unless explicitly
  justified.
- [ ] Move existing inline exceptions incrementally into flavor strategies,
  beginning with original-file/fix handling for Atlas and operation-specific
  CMIP6-decadal fixes. Preserve behavior while migrating, then remove project
  differences that are no longer necessary.
- [ ] Expose the selected project flavor and the reason for its processing-flow
  decision in diagnostic logs, so production behavior can be understood
  without reading the code.

## Explicit failure model

Rook currently turns many failures into a generic ``ProcessError``. Clients and
operators therefore cannot reliably distinguish an invalid spatial request from
a catalog lookup failure, an unavailable source, a dataset-format problem, a
fix failure, or an execution/resource failure.

- [ ] Define a small Rook exception hierarchy with stable categories such as
  request validation, spatial selection, temporal selection, catalog lookup,
  source access, dataset decoding, dataset fixes, processing, resource limits,
  and output publication. Avoid creating one exception type for every call
  site.
- [ ] Give every public failure a stable machine-readable code and a concise,
  user-safe message. Include actionable context such as the parameter, dataset
  ID, requested bounds, or processing phase where appropriate, without exposing
  private paths, credentials, or internal tracebacks.
- [ ] Map typed Rook exceptions deliberately onto WPS/OGC exception codes and
  locators. Preserve the original exception as the Python cause and retain the
  detailed traceback in service logs instead of flattening every failure to a
  string at the processing-flow boundary.
- [ ] Translate known clisops, catalog, Xarray, filesystem, fix-provider, and
  writer failures at the boundary where their meaning is still known. Unknown
  exceptions should remain an explicit internal-processing category.
- [ ] Return the same failure classification through synchronous WPS responses,
  asynchronous status documents, workflows, smoke-test helpers, and future
  status/metrics reporting.
- [ ] Add contract tests for each category, including the disjoint spatial case,
  empty catalog results, inaccessible sources, invalid datasets, failed fixes,
  memory/output limits, and unexpected internal errors. Assert both the public
  code/message and the preserved logged cause.

## Subset batching

- [ ] Evaluate the performance, encoding fidelity, peak memory use, and
  reliability of the first-batch on-disk size estimate on representative
  production requests, including 360-day calendars and project-specific
  metadata.
- [ ] Decide whether subset batch merging needs strict post-write output-size
  validation. Currently `clisops:write.file_size_limit` caps the estimated
  merge plan rather than the final file's measured size.
- [ ] Replace the subset batching module's local standard-library stream
  handler with centralized Rook/PyWPS logging. Ensure messages from Rook and
  clisops are routed consistently to the configured service or Slurm job logs
  without duplication.

## Pre-execution request validation

Requests submitted outside the CDS portal, in particular through the CDS API,
can pass several dataset identifiers to an operator such as subset even though
Rook normally supports one dataset per operation. Workflow references such as
``collection: inputs/pr`` can have the same effect because they currently
substitute the entire input value. These invalid requests may be accepted as
jobs and fail only after catalog resolution or processing has begun, producing
large, difficult-to-diagnose failure reports and wasting worker resources.

- [ ] Add a dedicated request-validation module invoked by the job controller
  after request parsing but before a job is queued or an operator begins
  processing. Give it a small, explicit interface shared by direct WPS/CDS API
  requests and workflow steps, and keep its first validation phase independent
  from catalog access and data processing.
- [ ] Identify and test the PyWPS ingress/dispatch integration point required to
  run structural validation before asynchronous job creation. Calling
  `validate` only from a process `_handler` does not count as early rejection if
  PyWPS has already accepted and persisted the job.
- [ ] Split validation deliberately into cheap structural/policy checks before
  queueing and semantic checks after catalog resolution but before source
  opening or compute. Document which phase owns each rule so `validate` cannot
  accidentally become an expensive execution path.
- [ ] Make validation rules easy to extend and test without adding conditionals
  to request handlers. Rules should declare the operators or request types they
  apply to and return structured validation failures with stable codes,
  messages, and parameter locators.
- [ ] Define and document the accepted dataset cardinality for every operator
  and request path, including direct WPS/CDS API requests and workflow steps.
  Keep singleton-only behavior explicit rather than interpreting a list
  differently according to its size or source.
- [ ] Implement dataset cardinality as the first validation rule. In
  particular, reject subset requests containing more than one dataset before
  job submission, catalog resolution, source opening, or clisops execution.
- [ ] Return a concise, user-safe validation error with a stable code and useful
  context: operator name, number of datasets received, expected cardinality,
  and guidance to submit one request per dataset. For workflows, also include
  the failing step ID. Expose the same classification through synchronous and
  asynchronous API responses.
- [ ] If multi-dataset workflows are supported, add explicit map/scatter
  semantics with per-dataset results and failures, bounded execution, stable
  output ordering, and an intentional fail-fast or partial-success policy.
- [ ] Add regression tests for direct CDS API/WPS subset requests and workflow
  inputs containing several CMIP6 dataset IDs. Assert that rejection happens
  before job execution and catalog access, verify the public error code and
  message, and, if mapping is implemented, prove that datasets are never
  combined into one logical source operation.

## Decadal concat batching

Status: source-path-level batching is implemented.

Production testing found that retaining normalized realization datasets across
batches caused approximately linear RSS growth. Opening and closing only the
relevant sources inside each yearly batch fixed the main problem: a seven-year,
ten-realization daily request with a Europe area selection stayed around 1.8 GB
RSS instead of growing toward OOM. Area pushdown reduces data before concat and
write, and the downstream subset is skipped when concat consumed every effective
selection. The largest transient allocation is now in the clisops NetCDF writer;
memory after its first write behaves mostly as a reusable high-water mark.

- [ ] Investigate whether the clisops writer peak can be reduced further.
- [ ] Safely minimize source files opened for each yearly batch where possible.
- [ ] Evaluate batch-size tuning for other variables, frequencies, and requests
  without area constraints.
- [ ] Reuse the diagnostics helpers for future memory and resource investigations.

## Packaging

- [ ] Publish the Woodpecker packages on conda-forge. The package request is
  pending while maintainers are on vacation; no Rook code change is currently
  needed.
- [ ] Once the packages are available, install Rook from a clean Conda
  environment, verify the Atlas and CMIP6-decadal plugins, and refresh the
  generated Conda lock/spec artifacts.

## Service status

The existing `health` process is a deliberately small OK/not-OK probe for load
balancers. Keep its `ROOK_HEALTH_OK` contract stable and add a separate,
synchronous `status` process for operational insight.

### Health probe improvements

- [ ] Define and document exactly what the lightweight `health` process proves
  (process execution and configured filesystem readability), which failures
  make it unhealthy, and how it differs from the richer `status` report.
- [ ] Review the default-empty `health.projects` configuration so a deployment
  cannot unintentionally report healthy without checking its required storage.
  Provide an explicit, validated configuration and useful startup diagnostics.
- [ ] Keep the probe fast and dependency-light, apply a short execution timeout,
  and return concise failure reasons without exposing paths or other sensitive
  deployment details.
- [ ] Retain the exact `ROOK_HEALTH_OK` success body and existing nginx endpoint
  for load-balancer compatibility. Add tests for timeouts, invalid
  configuration, partial filesystem failure, and response stability.

### First useful status report

- [ ] Define one versioned status-report model used by every output. Give the
  overall service and each check a `green`, `yellow`, or `red` state, a short
  public message, measurement time, and optional non-sensitive details.
- [ ] Return the report as JSON for monitoring and render the same report as a
  small, user-friendly HTML overview. Do not duplicate check logic in the HTML
  renderer.
- [ ] Report PyWPS database connectivity and job-state counts, including queued,
  running, succeeded, failed, and stale jobs. Include recent failure and timing
  summaries where they are cheap to calculate.
- [ ] Report Slurm availability and queue state, including pending/running job
  counts and useful reasons for blocked jobs. Make this check optional so Rook
  still works on deployments without Slurm.
- [ ] Report basic server signals such as process uptime, CPU/load, memory, and
  disk usage. Define configurable warning and failure thresholds.
- [ ] Report every configured Rook filesystem sentinel separately, rather than
  collapsing all projects into one OK/not-OK result.
- [ ] Report nginx access-log availability and freshness without making the
  whole report fail when logs are unavailable.
- [ ] Preserve partial results when a check times out or fails. Apply short
  per-check timeouts so the status page itself remains responsive.
- [ ] Avoid exposing filesystem paths, commands, credentials, internal error
  traces, or private job data in either public representation.
- [ ] Add nginx shortcuts for the HTML overview and JSON document (for example,
  `/status` and `/status.json`) while retaining the direct WPS execution URLs.
- [ ] Add unit tests for state aggregation, thresholds, redaction, JSON schema,
  and HTML rendering, plus smoke tests for the direct and nginx URLs.

### Later dashboard integration

- [ ] Show the current status report and live jobs before historical KPI charts.
- [ ] Separate collection, aggregation, health evaluation, and presentation so
  new metric sources do not need to be wired directly into the dashboard.
- [ ] Keep all PyWPS job states in usage data instead of limiting the dashboard
  to succeeded and failed requests.
- [ ] Add longer-term insights: success/failure rates, duration trends,
  recurring errors, download totals, worker saturation, and source freshness.
- [ ] Define retention and alert thresholds for stale jobs, failure rate, source
  freshness, and worker saturation.
- [ ] Replace the hard-coded multi-site registry with configured sites and
  authentication-aware collection.

## Reactivate storm tests

Make `tests/storm` useful for repeatable real-world testing on a dedicated test
server, while keeping expensive processing requests explicit and bounded.

- [ ] Fix the execute-template lookup: `common/wps.py` currently looks below
  `wps.py/templates` instead of the sibling `common/templates` directory.
- [ ] Update custom request reporting to the current Locust event API and add
  focused tests for accepted, succeeded, failed, malformed, and timed-out WPS
  responses.
- [ ] Take the target host, polling interval, and execution timeout from Locust
  options or environment variables; do not require editing the locustfile.
- [ ] Add a fast `meta` profile for health, status, capabilities, and process
  descriptions, with a documented headless command suitable for CI or a test
  server.
- [ ] Review the current collection IDs and time ranges against the test-server
  catalog. Keep a small known-good request per process and workflow.
- [ ] Separate lightweight validation from data-heavy scenarios with clear tags
  and conservative defaults. Require an explicit tag/profile for costly tests.
- [ ] Add a bounded `memory-regression` profile containing the AFR-22 multi-file
  daily subset and ten-member CMIP6-decadal concat cases. Verify successful
  outputs under the configured Slurm memory limit before adding concurrency.
- [ ] Add explicit load profiles for single-request baselines, fixed low
  concurrency, and gradual concurrency ramps. Keep request counts, spawn rates,
  maximum concurrency, and test duration configurable, with safe defaults.
- [ ] Correlate every request with its PyWPS and Slurm job identifiers and record
  queue time, execution time, peak RSS/MaxRSS, exit state, timeout, and OOM
  events. Preserve enough context to distinguish service, scheduler, and data
  processing failures.
- [ ] Define initial acceptance criteria from measured baselines: zero OOM kills,
  no lost or malformed responses, bounded failure/timeout rates, and stable peak
  RSS as concurrency increases. Keep runtime thresholds configurable until
  representative production baselines exist.
- [ ] Add an opt-in tuning matrix for Rook batch memory aims and clisops
  ``chunk_memory_limit`` values without running the full Cartesian product by
  default.
- [ ] Validate output links and result metadata after `ProcessSucceeded`, not
  only the final WPS state.
- [ ] Add output cleanup and retention controls so repeated stress runs do not
  exhaust shared storage; default to preserving only reports and failed-run
  evidence.
- [ ] Produce a short HTML/CSV report and document how to keep it as deployment
  evidence without committing generated results.
- [ ] Add a Make target and refresh `tests/storm/README.md` with installation,
  interactive, headless, and safe remote-server examples.

## Processing maintenance

- [ ] Continue focused cleanup of operators, `rook.pflow`, `workflow.py`, and WPS
  process modules while preserving the public WPS interface.
- [ ] Revisit the Woodpecker provider lifecycle after production experience,
  especially the CMIP6-decadal `prepare(...)` phase.
- [ ] Replace hard-coded smoke workflow documents with small Python builders.
- [ ] Add live S3 integration coverage and future S3/Zarr output support.
- [ ] Continue mini-ESGF replacement work without making it a release blocker.
