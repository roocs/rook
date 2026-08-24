import numpy as np
import xarray as xr

from rook.pflow.spatial import SpatialRelation, area_relation, dataset_area_relation


def rectilinear_dataset(longitudes=(-10, 0, 10), latitudes=(40, 50, 60)):
    return xr.Dataset(
        coords={"lon": np.asarray(longitudes), "lat": np.asarray(latitudes)}
    )


def test_area_contains_dataset_extent():
    relation = area_relation(rectilinear_dataset(), "-20,30,20,70")

    assert relation is SpatialRelation.CONTAINS


def test_area_only_partly_overlaps_dataset_extent():
    relation = area_relation(rectilinear_dataset(), "0,50,20,70")

    assert relation is SpatialRelation.PARTIAL


def test_area_is_disjoint_from_dataset_extent():
    relation = area_relation(rectilinear_dataset(), "30,-20,50,20")

    assert relation is SpatialRelation.DISJOINT


def test_longitude_frames_are_normalized():
    dataset = rectilinear_dataset(longitudes=(350, 0, 10))

    assert area_relation(dataset, "-20,30,20,70") is SpatialRelation.CONTAINS


def test_monotonic_coordinates_keep_their_natural_longitude_extent():
    dataset = rectilinear_dataset(longitudes=(0, 187.5))

    assert area_relation(dataset, "0,30,187.5,70") is SpatialRelation.CONTAINS


def test_dateline_crossing_dataset_and_request():
    dataset = rectilinear_dataset(longitudes=(170, 175, -180, -175, -170))

    assert area_relation(dataset, "160,30,-160,70") is SpatialRelation.CONTAINS
    assert area_relation(dataset, "-20,30,20,70") is SpatialRelation.DISJOINT


def test_curvilinear_coordinates_are_supported():
    dataset = xr.Dataset(
        coords={
            "lat": (("y", "x"), np.array([[40, 41], [50, 51]])),
            "lon": (("y", "x"), np.array([[-10, 0], [-9, 1]])),
        }
    )

    assert area_relation(dataset, "-20,30,20,60") is SpatialRelation.CONTAINS


def test_missing_spatial_coordinates_are_unknown():
    assert area_relation(xr.Dataset(), "-20,30,20,70") is SpatialRelation.UNKNOWN


def test_oversized_coordinates_fall_back_to_normal_processing(monkeypatch):
    monkeypatch.setattr("rook.pflow.spatial._MAX_COORDINATE_VALUES", 2)

    relation = area_relation(rectilinear_dataset(), "-20,30,20,70")

    assert relation is SpatialRelation.UNKNOWN


def test_dataset_relation_opens_coordinate_metadata_only(tmp_path):
    path = tmp_path / "small.nc"
    rectilinear_dataset().to_netcdf(path)

    assert dataset_area_relation(path, "-20,30,20,70") is SpatialRelation.CONTAINS
