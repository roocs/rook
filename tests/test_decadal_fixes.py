import numpy as np
import pytest
import xarray as xr

import builtins

from rook.fixes.providers import (
    FixContext,
    WOODPECKER_CMIP6_DECADAL_RECIPE_ID,
    WoodpeckerDatasetFixProvider,
)
from rook.utils.decadal_fixes import (
    apply_decadal_fixes,
)

cftime = pytest.importorskip("cftime")
woodpecker_testing = pytest.importorskip("woodpecker.testing")
pytest.importorskip("woodpecker_cmip6_decadal_plugin")

DECADAL_DS_ID = (
    "c3s-cmip6-decadal.DCPP.MPI-M.MPI-ESM1-2-HR.dcppA-hindcast."
    "s1960-r1i1p1f1.Omon.tos.gn.v20200101"
)


def make_representative_decadal_sample():
    source_name = f"{DECADAL_DS_ID}.nc"
    dataset = woodpecker_testing.make_cmip6_decadal(
        overrides={
            "dataset_id": DECADAL_DS_ID.replace("c3s-cmip6-decadal.", "CMIP6."),
            "source_file": source_name,
            "source_name": source_name,
            "realization_index": 1,
            "startdate": "s1960",
            "sub_experiment_id": "s1960",
        }
    )
    dataset = dataset.isel(time=slice(0, 2))
    dataset = dataset.assign_coords(
        time=np.array(
            [
                cftime.DatetimeGregorian(1960, 11, 16),
                cftime.DatetimeGregorian(1960, 12, 16),
            ],
            dtype=object,
        )
    )
    dataset["time"].attrs["long_name"] = "time"
    dataset["time"].encoding["calendar"] = "standard"
    return dataset


def roundtrip_dataset(dataset, path):
    dataset.to_netcdf(path)
    loaded = xr.open_dataset(path)
    loaded.load()
    loaded.close()
    return loaded


def dataset_difference_report(left, right):
    differences = []
    if set(left.dims) != set(right.dims):
        differences.append(f"dims differ: {dict(left.dims)!r} != {dict(right.dims)!r}")
    if set(left.coords) != set(right.coords):
        differences.append(
            f"coords differ: {sorted(left.coords)!r} != {sorted(right.coords)!r}"
        )
    if set(left.data_vars) != set(right.data_vars):
        differences.append(
            f"data_vars differ: {sorted(left.data_vars)!r} != {sorted(right.data_vars)!r}"
        )

    for name in sorted(set(left.variables) & set(right.variables)):
        left_var = left[name]
        right_var = right[name]
        if left_var.dims != right_var.dims:
            differences.append(f"{name}.dims: {left_var.dims!r} != {right_var.dims!r}")
        if left_var.dtype != right_var.dtype:
            differences.append(
                f"{name}.dtype: {left_var.dtype!r} != {right_var.dtype!r}"
            )
        if left_var.attrs != right_var.attrs:
            differences.append(
                f"{name}.attrs: {left_var.attrs!r} != {right_var.attrs!r}"
            )
        try:
            xr.testing.assert_equal(left_var, right_var)
        except AssertionError as exc:
            differences.append(f"{name}.values: {exc}")

    if left.attrs != right.attrs:
        differences.append(f"attrs differ: {left.attrs!r} != {right.attrs!r}")

    return "\n".join(differences)


def assert_identical_with_report(left, right):
    try:
        xr.testing.assert_identical(left, right)
    except AssertionError as exc:
        report = dataset_difference_report(left, right)
        raise AssertionError(f"{exc}\n\nExact differences:\n{report}") from exc


def test_woodpecker_decadal_recipe_id_is_cmip6_decadal_full():
    assert WOODPECKER_CMIP6_DECADAL_RECIPE_ID == "cmip6_decadal.full"


def test_woodpecker_decadal_fixes_raise_clear_error_when_woodpecker_missing(
    monkeypatch,
):
    real_import = builtins.__import__

    def block_woodpecker_import(name, *args, **kwargs):
        if name == "woodpecker":
            raise ImportError("blocked woodpecker import")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", block_woodpecker_import)

    with pytest.raises(ImportError, match="Woodpecker is required"):
        WoodpeckerDatasetFixProvider().apply(
            xr.Dataset(),
            context=FixContext(
                dataset_id=DECADAL_DS_ID,
                recipe_id=WOODPECKER_CMIP6_DECADAL_RECIPE_ID,
            ),
        )


def test_woodpecker_decadal_fixes_match_legacy_rook_output(tmp_path):
    dataset = make_representative_decadal_sample()

    legacy = apply_decadal_fixes(DECADAL_DS_ID, dataset.copy(deep=True))
    woodpecker = WoodpeckerDatasetFixProvider().apply(
        dataset.copy(deep=True),
        context=FixContext(
            dataset_id=DECADAL_DS_ID,
            recipe_id=WOODPECKER_CMIP6_DECADAL_RECIPE_ID,
        ),
    )

    legacy_output = roundtrip_dataset(legacy, tmp_path / "legacy.nc")
    woodpecker_output = roundtrip_dataset(woodpecker, tmp_path / "woodpecker.nc")

    assert_identical_with_report(legacy_output, woodpecker_output)
