"""Subset-to-file alignment checks."""

from pathlib import Path

from clisops.parameter import time_components_parameter, time_parameter
from clisops.project_utils import url_to_file_path
from clisops.utils.time_utils import to_isoformat

import xarray as xr


class SubsetAlignmentChecker:
    def __init__(self, input_files, inputs):
        self.input_files = sorted(input_files)
        self.is_aligned = False
        self.aligned_files = []

        self._deduce_alignment(inputs)

    def _deduce_alignment(self, inputs):
        if any(inputs.get(key) for key in ("area", "level", "shape")):
            return

        time = inputs.get("time", None)
        time_components = inputs.get("time_components", None)

        if time_components:
            bounds = self._whole_year_component_bounds(time, time_components)
            if bounds is None:
                return
            self._check_time_alignment(*bounds)
            return

        # add in a catch for if time bounds are None
        # this means is_aligned = True and all files are needed
        if time is None:
            self.is_aligned = True
            self.aligned_files = self.input_files
            return

        else:
            start, end = time_parameter.TimeParameter(time).get_bounds()
            self._check_time_alignment(start, end)

    def _whole_year_component_bounds(self, time, time_components):
        """Return effective bounds for consecutive whole-year selections."""
        components = time_components_parameter.TimeComponentsParameter(
            time_components
        ).value
        if set(components) != {"year"}:
            return None

        years = sorted(set(components["year"]))
        if not years or years != list(range(years[0], years[-1] + 1)):
            return None

        start = f"{years[0]:04d}-01-01T00:00:00"
        end = f"{years[-1]:04d}-12-31T23:59:59"
        if time:
            time_start, time_end = time_parameter.TimeParameter(time).get_bounds()
            start = max(start, time_start)
            end = min(end, time_end)

        return (start, end) if start <= end else None

    def _get_file_times(self, fpath):
        # get start and end times from the time dimension in the file

        # convert url to file path if needed
        if Path(fpath).as_posix().startswith("http"):
            fpath = url_to_file_path(fpath)

        try:
            time_coder = xr.coders.CFDatetimeCoder(use_cftime=True)
            ds = xr.open_dataset(fpath, decode_times=time_coder)
        except (AttributeError, TypeError):
            ds = xr.open_dataset(fpath, use_cftime=True)
        start = to_isoformat(ds.time.values[0])
        end = to_isoformat(ds.time.values[-1])
        ds.close()
        return start, end

    def _check_time_alignment(self, start, end):
        """
        Check if data files can be aligned with start and end time.

        Loops through all data files to check if the `start` and `end` can be aligned
        with the exact start or end time in the file(s).

        If both the `start` and the `end` are aligned then the following properties
        are set:
         - self.aligned_files = [list of matching files in range]
         - self.is_aligned = True

        If the `start` is before the start time of the first file and/or
        the `end` is after the end time of the last file then that is considered
        a valid match to the required time range.
        """
        aligned_files = self._find_aligned_files(start, end)
        if aligned_files is not None:
            self.is_aligned = True
            self.aligned_files = aligned_files

    def _find_aligned_files(self, start, end):
        """Return files that exactly cover a requested range, if any."""
        overlapping = []
        for fpath in self.input_files:
            fstart, fend = self._get_file_times(fpath)
            if fstart > end:
                break
            if fend >= start:
                overlapping.append((fpath, fstart, fend))

        if not overlapping:
            return None

        # A request may extend beyond available data. In that case the usable
        # data boundary is still considered aligned.
        start = max(start, overlapping[0][1])
        end = min(end, overlapping[-1][2])

        if not any(fstart == start for _, fstart, _ in overlapping):
            return None
        if not any(fend == end for _, _, fend in overlapping):
            return None

        return [fpath for fpath, _, _ in overlapping]
