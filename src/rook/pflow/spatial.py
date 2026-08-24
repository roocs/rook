"""Cheap spatial checks used when deciding whether subsetting is necessary."""

from enum import Enum
from pathlib import Path

import numpy as np
import xarray as xr
from clisops.core.subset import get_lat, get_lon
from clisops.exceptions import InvalidProject
from clisops.parameter.area_parameter import AreaParameter
from clisops.project_utils import url_to_file_path

_TOLERANCE = 1e-6
_MAX_COORDINATE_VALUES = 10_000_000


class SpatialRelation(Enum):
    """Relationship between a requested area and a dataset bounding box."""

    CONTAINS = "contains"
    DISJOINT = "disjoint"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


def dataset_area_relation(path, area):
    """Inspect one dataset's coordinates and classify a requested area."""
    try:
        if Path(path).as_posix().startswith("http"):
            path = url_to_file_path(path)
        with xr.open_dataset(path, decode_times=False) as dataset:
            return area_relation(dataset, area)
    except (InvalidProject, KeyError, OSError, TypeError, ValueError):
        return SpatialRelation.UNKNOWN


def area_relation(dataset, area):
    """Classify an area against the latitude/longitude extent of a dataset."""
    try:
        bounds = AreaParameter(area).asdict()
        latitude = get_lat(dataset)
        longitude = get_lon(dataset)
    except (AttributeError, KeyError, TypeError, ValueError):
        return SpatialRelation.UNKNOWN

    if (
        latitude.size > _MAX_COORDINATE_VALUES
        or longitude.size > _MAX_COORDINATE_VALUES
    ):
        return SpatialRelation.UNKNOWN

    latitudes = _finite_values(latitude)
    longitudes = _finite_values(longitude)
    if latitudes is None or longitudes is None:
        return SpatialRelation.UNKNOWN

    requested_lat = tuple(sorted(bounds["lat_bnds"]))
    dataset_lat = (float(latitudes.min()), float(latitudes.max()))
    requested_lon = _longitude_arc(bounds["lon_bnds"])
    dataset_lon = _dataset_longitude_arc(longitude, longitudes)

    if _intervals_disjoint(requested_lat, dataset_lat) or not _arcs_overlap(
        requested_lon, dataset_lon
    ):
        return SpatialRelation.DISJOINT

    if _interval_contains(requested_lat, dataset_lat) and _arc_contains(
        requested_lon, dataset_lon
    ):
        return SpatialRelation.CONTAINS

    return SpatialRelation.PARTIAL


def _finite_values(coordinate):
    """Return finite coordinate values, or None for unsupported coordinates."""
    try:
        values = np.asarray(coordinate.values, dtype=float).ravel()
    except (TypeError, ValueError):
        return None
    values = values[np.isfinite(values)]
    return values if values.size else None


def _longitude_arc(bounds):
    """Return a west-to-east circular arc as (start, span) in degrees."""
    west, east = (float(value) for value in bounds)
    difference = east - west
    span = 360.0 if abs(difference) >= 360.0 else difference % 360.0
    return west % 360.0, span


def _dataset_longitude_arc(coordinate, values):
    """Return the natural longitude extent, including dateline-crossing grids."""
    if coordinate.ndim == 1:
        differences = np.diff(np.asarray(coordinate.values, dtype=float))
        monotonic = np.all(differences >= 0) or np.all(differences <= 0)
        if monotonic:
            return _longitude_arc((values.min(), values.max()))

    points = np.unique(np.mod(values, 360.0))
    if points.size == 1:
        return float(points[0]), 0.0

    gaps = np.diff(np.concatenate((points, points[:1] + 360.0)))
    largest_gap = int(np.argmax(gaps))
    start = float(points[(largest_gap + 1) % points.size])
    return start, float(360.0 - gaps[largest_gap])


def _intervals_disjoint(first, second):
    return first[1] < second[0] - _TOLERANCE or second[1] < first[0] - _TOLERANCE


def _interval_contains(outer, inner):
    return outer[0] <= inner[0] + _TOLERANCE and outer[1] >= inner[1] - _TOLERANCE


def _arc_segments(arc):
    """Split a circular arc into ordinary intervals in the 0..360 frame."""
    start, span = arc
    if span >= 360.0 - _TOLERANCE:
        return [(0.0, 360.0)]
    end = start + span
    if end <= 360.0:
        return [(start, end)]
    return [(start, 360.0), (0.0, end - 360.0)]


def _arcs_overlap(first, second):
    return any(
        not _intervals_disjoint(left, right)
        for left in _arc_segments(first)
        for right in _arc_segments(second)
    )


def _arc_contains(outer, inner):
    outer_segments = _arc_segments(outer)
    return all(
        any(
            _interval_contains(outer_segment, segment)
            for outer_segment in outer_segments
        )
        for segment in _arc_segments(inner)
    )
