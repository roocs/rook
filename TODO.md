# Rook TODO

Only unfinished or deliberately deferred work belongs here. Completed work is
documented in `CHANGELOG.rst`.

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

## Revive storm tests

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
- [ ] Validate output links and result metadata after `ProcessSucceeded`, not
  only the final WPS state.
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
