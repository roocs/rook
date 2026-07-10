import pytest
import xarray as xr

from rook.fixes.legacy.atlas import apply_atlas_fixes
from rook.fixes.providers import (
    FixContext,
    WOODPECKER_ATLAS_RECIPE_ID,
    WoodpeckerDatasetFixProvider,
)

pytest.importorskip("woodpecker")
pytest.importorskip("woodpecker_atlas_plugin")

ATLAS_DS_ID = "c3s-ipcc-atlas.tnn.CMIP6.historical.mon"


def make_representative_atlas_sample():
    dataset = xr.Dataset(
        {"tas": ("time", [280.0, 281.0])},
        coords={"time": [0, 1], "member_id": ("member_id", ["r1i1p1f1"])},
    )
    for var in list(dataset.coords) + list(dataset.data_vars):
        dataset[var].encoding["_FillValue"] = "missing"
    dataset["member_id"].encoding.update(
        {"zlib": True, "shuffle": True, "complevel": 5}
    )
    dataset["tas"].encoding.update({"zlib": True, "shuffle": True, "complevel": 5})
    return dataset


def encoding_difference_report(left, right):
    differences = []
    for name in sorted(set(left.variables) | set(right.variables)):
        if name not in left or name not in right:
            differences.append(f"{name}: variable missing from one dataset")
            continue
        if left[name].encoding != right[name].encoding:
            differences.append(
                f"{name}.encoding: {left[name].encoding!r} != {right[name].encoding!r}"
            )
    return "\n".join(differences)


def assert_same_dataset_and_encoding(left, right):
    try:
        xr.testing.assert_identical(left, right)
        assert encoding_difference_report(left, right) == ""
    except AssertionError as exc:
        report = encoding_difference_report(left, right)
        raise AssertionError(f"{exc}\n\nExact encoding differences:\n{report}") from exc


def test_woodpecker_atlas_recipe_id_is_atlas_basic():
    assert WOODPECKER_ATLAS_RECIPE_ID == "c3s.atlas"


def test_woodpecker_atlas_fixes_match_legacy_rook_output():
    dataset = make_representative_atlas_sample()

    legacy = apply_atlas_fixes(ATLAS_DS_ID, dataset.copy(deep=True))
    woodpecker = WoodpeckerDatasetFixProvider().apply(
        dataset.copy(deep=True),
        context=FixContext(
            dataset_id=ATLAS_DS_ID,
            recipe_id=WOODPECKER_ATLAS_RECIPE_ID,
        ),
    )

    assert_same_dataset_and_encoding(legacy, woodpecker)
