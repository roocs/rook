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

### Atlas fix-only path and persistent cache

Atlas catalog resolution can yield the complete source time range because fixes
must be applied before files can be returned. Avoid running clisops subset when
the effective request is otherwise a semantic pass-through, and use the
available 1 TB SSD for durable fixed Atlas outputs.

- [ ] Measure Atlas requests separately to confirm the time spent opening,
  applying Woodpecker fixes, running a no-op subset, and writing. Cover full-time
  requests with no area as well as real time, level, component, and area
  selections.
- [ ] Add an explicit processing-flow decision for "fix and write" that bypasses
  clisops subset only when every requested selection is already aligned with the
  resolved source. Treat the absence of an area alone as insufficient: time,
  time components, level, output type, split method, and any future subset
  parameter must also be proven to be no-ops.
- [ ] Verify that fix-only output is byte/metadata/encoding-equivalent to the
  current fixed subset output for pass-through requests, including provenance,
  filenames, file-size splitting, calendars, bounds, and Atlas variants.
- [ ] Define a small backend-neutral artifact-cache abstraction before adding a
  cache dependency. Keep Atlas and processing-flow code limited to operations
  such as lookup/materialize, publish, invalidate, cull, and statistics; do not
  expose DiskCache keys, internal paths, locks, or file handles outside the
  adapter.
- [ ] Provide a disabled/no-op backend and select cache backends by configuration
  so caching remains optional. Make unavailable optional dependencies produce a
  clear configuration error, while runtime cache failures fall back safely to
  uncached processing where possible.
- [ ] Implement DiskCache as the first optional backend and pin its dependency.
  Configure a byte-based size limit and least-recently-used eviction, store the
  actual artifact bytes rather than unaccounted external path strings, and run a
  complete cull after publishing large entries.
- [ ] Design canonical backend-independent cache keys from dataset/source
  identity and freshness plus the Woodpecker recipe, plugin/package versions,
  and output-affecting settings so stale fixes cannot be served after source or
  recipe changes.
- [ ] Populate entries with a per-key lock and atomic publish so concurrent
  misses perform the work once and readers never observe partial files. On a
  hit, validate and materialize the entry into the request output directory by
  hard link when safe, otherwise copy it, so later eviction cannot break a
  published download.
- [ ] Use cached fixed Atlas files as inputs to real spatial, temporal, or level
  subsets, so the cache avoids repeated fixes even when the subset itself cannot
  be skipped.
- [ ] Define cache capacity, free-space reserve, permissions, corruption
  recovery, explicit invalidation, and least-recently-used cleanup for the 1 TB
  disk. Record hit/miss, bytes, build time, last access, and eviction metrics.
- [ ] Estimate the complete fixed Atlas footprint and decide whether to pre-warm
  all current datasets or fill on demand. If pre-warming, make it resumable,
  bounded, and safe alongside live requests.
- [ ] Add unit and integration coverage for cache hit, miss, concurrent miss,
  invalidation after source/recipe changes, corrupt/incomplete entries, disk-full
  fallback, and equivalence with uncached processing.
- [ ] Add backend contract tests covering lookup, access-time refresh,
  publication, materialization, invalidation, byte accounting, eviction,
  concurrency, and failure semantics. Run the same suite against the no-op and
  DiskCache adapters so another optional backend can be evaluated or introduced
  without changing Atlas processing.
- [ ] Keep cache observability backend-neutral and expose backend name, capacity,
  used bytes, entry count, hits, misses, evictions, corruptions, and publish
  failures through logs and the future status report.

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

## Multi-dataset workflow inputs

Workflow references such as ``collection: inputs/pr`` currently substitute the
entire input value. A request containing many dataset identifiers can therefore
invoke one operator with all datasets even when the request producer intended
one independent operation per dataset. This creates large, difficult-to-diagnose
failure reports and unclear retry semantics.

- [ ] Define and document whether workflow operators support multi-dataset
  collections, implicit mapping, or singleton inputs only. Keep the behavior
  explicit rather than interpreting a list differently according to its size.
- [ ] As a minimum safeguard, detect a multi-dataset collection during workflow
  validation for operators that require a single dataset and reject it before
  catalog resolution or processing. Return a concise error containing the step
  ID, operator name, number of datasets received, expected cardinality, and
  guidance to submit one workflow per dataset.
- [ ] If multi-dataset workflows are supported, add explicit map/scatter
  semantics with per-dataset results and failures, bounded execution, stable
  output ordering, and an intentional fail-fast or partial-success policy.
- [ ] Add regression tests using a workflow input containing several CMIP6
  dataset IDs. Cover the validation error and, if mapping is implemented, prove
  that datasets are never combined into one logical source operation.

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
