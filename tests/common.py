"""Common helpers for tests."""

import pytest

from rook.io.datasets import DatasetSource

SYNTHETIC_CMIP6_DECADAL_DATASET_ID = (
    "c3s-cmip6-decadal.DCPP.MPI-M.MPI-ESM1-2-HR.dcppA-hindcast."
    "s1960-r1i1p1f1.Omon.tos.gn.v20200101"
)


def make_synthetic_cmip6_decadal_source(tmp_path):
    woodpecker_testing = pytest.importorskip("woodpecker.testing")
    pytest.importorskip("woodpecker_cmip6_decadal_plugin")
    dataset = woodpecker_testing.make_cmip6_decadal(seed=1).isel(time=slice(0, 2))
    paths = []

    for index in range(2):
        path = tmp_path / f"synthetic-decadal-{index}.nc"
        dataset.isel(time=[index]).to_netcdf(path)
        paths.append(path.as_posix())

    return DatasetSource(SYNTHETIC_CMIP6_DECADAL_DATASET_ID, paths)
