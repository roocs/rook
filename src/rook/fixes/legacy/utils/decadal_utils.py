"""Utility functions for legacy decadal fixes."""

import re
from datetime import datetime

import cftime


def get_time_calendar(ds_id, ds):
    """Get the calendar from the dataset time axis."""
    times = ds.time.values
    return times[0].calendar


def get_start_date(ds_id, ds):
    """Get start date inferred from decadal dataset id."""
    year = ds_id.split(".")[5].split("-")[0].lstrip("s")
    return datetime(int(year), 11, 1, 0, 0).isoformat()


def get_sub_experiment_id(ds_id, ds):
    """Get sub-experiment identifier from start date."""
    sd = datetime.fromisoformat(get_start_date(ds_id, ds))
    return f"s{sd.year}{sd.month}"


def get_reftime(ds_id, ds):
    """Get reference time for decadal forecast."""
    default_sd = get_start_date(ds_id, ds)

    start_date = ds.attrs.get("startdate", None)

    if not start_date:
        start_date = default_sd
    else:
        regex = re.compile(r"^s(\d{4})(\d{2})$")
        match = regex.match(start_date)

        default = datetime.fromisoformat(default_sd)

        if match:
            items = match.groups()
            try:
                start_date = datetime(
                    int(items[0]),
                    int(items[1]),
                    default.day,
                    default.hour,
                    default.minute,
                    default.second,
                ).isoformat()
            except ValueError:
                start_date = default_sd.isoformat()
        else:
            start_date = default_sd.isoformat()

    return start_date


def get_lead_times(ds_id, ds):
    """Get lead times in days relative to forecast reference time."""
    start_date = datetime.fromisoformat(get_start_date(ds_id, ds))

    cal = get_time_calendar(ds_id, ds)
    reftime = cftime.datetime(
        start_date.year,
        start_date.month,
        start_date.day,
        start_date.hour,
        start_date.minute,
        start_date.second,
        calendar=cal,
    )

    lead_times = []
    for time in ds.time.values:
        td = time - reftime
        lead_times.append(td.days)

    return lead_times
