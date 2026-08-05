# Rook TODO

This file tracks work after the completed `v1.3.0` release. Release mechanics
and the Woodpecker migration are recorded in `CHANGELOG.rst` and Git history
rather than kept here as a stale release checklist.

## Operational visibility

Current state: the usage process collects request data from the PyWPS database
and downloads from nginx access logs. The dashboard derives historical KPIs
from those CSV files and limits its job views to succeeded and failed requests.
It does not yet expose live/queued/stale jobs, collector health, worker state,
or host/service health.

### Dashboard and usage refactor

- [ ] Separate collection, aggregation, health evaluation, and presentation so
  new metric sources do not need to be wired directly into the dashboard.
- [ ] Keep all PyWPS job states in usage data instead of limiting the dashboard
  to succeeded and failed requests.
- [ ] Add a machine-readable insight report with job counts, active and stale
  jobs, success/failure rates, durations, recurring errors, and download totals.
- [ ] Report PyWPS database, nginx-log collection, and configured Rook health
  checks separately; preserve partial results when nginx logs are unavailable.
- [ ] Show current jobs and service health before historical KPI charts.
- [ ] Add scheduler/worker queue metrics once the production execution backend
  and its stable monitoring interface are selected.
- [ ] Add host/container signals (CPU, memory, disk, process restarts) from the
  deployment monitoring system rather than inferring them from request logs.
- [ ] Define alert thresholds and retention for stale jobs, failure rate, source
  freshness, and worker saturation.
- [ ] Replace the hard-coded multi-site registry with configured sites and
  authentication-aware collection.

## Processing maintenance

- Continue focused cleanup of operators, `rook.pflow`, `workflow.py`, and WPS
  process modules while preserving the public WPS interface.
- Revisit the Woodpecker provider lifecycle after production experience,
  especially the CMIP6-decadal `prepare(...)` phase.
- Replace hard-coded smoke workflow documents with small Python builders.
- Add live S3 integration coverage and future S3/Zarr output support.
- Continue mini-ESGF replacement work without making it a release blocker.
