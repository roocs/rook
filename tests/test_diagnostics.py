import os
from pathlib import Path
import sys

import xarray as xr

import rook.diagnostics as diagnostics
import rook.diagnostics.memory as memory_diagnostics


def test_memory_checkpoint_reads_proc_status_and_flushes_stderr(monkeypatch, tmp_path):
    status = tmp_path / "status"
    status.write_text("Name:\tpython\nVmRSS:\t123456 kB\n")
    calls = []

    monkeypatch.setattr(memory_diagnostics, "_STATUS_PATH", status)
    monkeypatch.setattr(
        "builtins.print",
        lambda message, **kwargs: calls.append((message, kwargs)),
    )

    diagnostics.memory_checkpoint("before test stage", "group=example")

    assert calls == [
        (
            f"[rook-diagnostic] pid={os.getpid()} VmRSS: 123456 kB "
            "before test stage | group=example",
            {"file": sys.stderr, "flush": True},
        )
    ]


def test_dataset_signature_reports_decadal_fix_markers(monkeypatch, capsys):
    monkeypatch.setattr(
        memory_diagnostics, "_STATUS_PATH", Path("/missing/proc/status")
    )
    dataset = xr.Dataset(
        {
            "tas": ("time", [280.0, 281.0]),
            "realization": xr.DataArray(1),
        },
        coords={
            "time": [0, 1],
            "reftime": xr.DataArray(0),
            "leadtime": ("time", [0.0, 1.0]),
        },
        attrs={
            "dataset_id": "CMIP6.DCPP.example",
            "startdate": "s1962",
            "sub_experiment_id": "s1962",
            "forcing_description": "set by recipe",
            "physics_description": "set by recipe",
            "initialization_description": "set by recipe",
        },
    )
    dataset.time.attrs["long_name"] = "valid_time"
    dataset.time.encoding["calendar"] = "standard"
    dataset.reftime.attrs["standard_name"] = "forecast_reference_time"
    dataset.leadtime.attrs.update({"standard_name": "forecast_period", "units": "days"})

    diagnostics.dataset_signature(
        "after Woodpecker apply",
        dataset,
        identity="realization-1",
        coordinate_names=("time", "reftime", "leadtime", "realization"),
        attribute_names=("dataset_id", "startdate", "sub_experiment_id"),
        presence_attributes=(
            "forcing_description",
            "physics_description",
            "initialization_description",
        ),
    )

    message = capsys.readouterr().err
    assert "VmRSS: unavailable after Woodpecker apply" in message
    assert "identity=realization-1" in message
    assert "long_name=valid_time" in message
    assert "calendar=standard" in message
    assert "standard_name=forecast_reference_time" in message
    assert "standard_name=forecast_period" in message
    assert "startdate=s1962" in message
    assert "sub_experiment_id=s1962" in message
    assert "forcing_description=set" in message
