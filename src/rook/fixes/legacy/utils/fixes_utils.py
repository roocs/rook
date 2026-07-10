"""Shared helpers for legacy fixes."""

import cftime
import xarray as xr


def convert_calendar_to_gregorian(
    ds: xr.Dataset, reference_date="1850-01-01"
) -> xr.Dataset:
    """Convert proleptic Gregorian time coordinates to Gregorian coordinates."""
    original_time = ds.time.values
    new_time = [
        cftime.DatetimeGregorian(t.year, t.month, t.day, t.hour, t.minute, t.second)
        for t in original_time
    ]
    ds = ds.assign_coords(time=("time", new_time))

    if "time_bnds" in ds:
        bnds = ds["time_bnds"].values
        new_bnds = []
        for start, end in bnds:
            new_start = cftime.DatetimeGregorian(
                start.year,
                start.month,
                start.day,
                start.hour,
                start.minute,
                start.second,
            )
            new_end = cftime.DatetimeGregorian(
                end.year,
                end.month,
                end.day,
                end.hour,
                end.minute,
                end.second,
            )
            new_bnds.append([new_start, new_end])
        ds["time_bnds"].values = new_bnds
        ds["time_bnds"].encoding.update(
            {
                "calendar": "gregorian",
                "units": f"days since {reference_date}",
                "dtype": "float64",
            }
        )

    ds.time.encoding.update(
        {
            "calendar": "gregorian",
            "units": f"days since {reference_date}",
            "dtype": "float64",
        }
    )

    return ds
