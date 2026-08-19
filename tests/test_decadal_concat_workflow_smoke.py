"""Small end-to-end regression for decadal concat workflow optimization."""

from pathlib import Path

import pytest
import xarray as xr

import rook.operations.concat as concat_mod
from rook.io.datasets import DatasetSource
from rook.workflow import Workflow

woodpecker_testing = pytest.importorskip("woodpecker.testing")
pytest.importorskip("woodpecker_cmip6_decadal_plugin")

DATASET_ID = (
    "c3s-cmip6-decadal.DCPP.MPI-M.MPI-ESM1-2-HR.dcppA-hindcast."
    "s1960-{variant}.Omon.tos.gn.v20200101"
)


def _make_sources(tmp_path):
    sources = []
    for realization in (1, 2):
        variant = f"r{realization}i1p1f1"
        dataset_id = DATASET_ID.format(variant=variant)
        paths = []
        for year in (2000, 2001):
            filename = (
                "tos_Omon_MPI-ESM1-2-HR_dcppA-hindcast_"
                f"s1960-{variant}_gn_{year}0101-{year}1201.nc"
            )
            dataset = woodpecker_testing.make_cmip6_decadal(seed=realization)
            dataset = dataset.assign_coords(
                time=xr.date_range(f"{year}-01-01", periods=12, freq="MS")
            )
            dataset.attrs.update(
                dataset_id=dataset_id.replace("c3s-cmip6-decadal.", "CMIP6."),
                source_file=filename,
                source_name=filename,
                variant_label=variant,
                realization_index=realization,
            )
            path = tmp_path / filename
            dataset.to_netcdf(path)
            paths.append(path.as_posix())
        sources.append(DatasetSource(dataset_id, paths))
    return sources


def test_decadal_concat_workflow_batches_sources_and_bypasses_subset(
    monkeypatch, tmp_path
):
    sources = _make_sources(tmp_path)
    output_dir = tmp_path / "concat_smoke"
    output_dir.mkdir()
    opened = []
    closed = []
    fix_calls = []

    original_normalise = concat_mod.normalise.normalise_file_groups
    original_opener = concat_mod.normalise.open_lazy_xr_dataset

    def tracked_opener(path):
        dataset = original_opener(path)
        key = Path(path).name
        opened.append(key)
        close_dataset = dataset._close

        def close():
            close_dataset()
            closed.append(key)

        dataset.set_close(close)
        return dataset

    def tracked_normalise(collection, **kwargs):
        return original_normalise(collection, opener=tracked_opener, **kwargs)

    monkeypatch.setattr(
        concat_mod.normalise, "normalise_file_groups", tracked_normalise
    )

    provider = concat_mod.get_dataset_fix_provider()

    class TrackingProvider:
        def prepare(self, dataset, *, context=None):
            fix_calls.append(("prepare", context.phase))
            return provider.prepare(dataset, context=context)

        def apply(self, dataset, *, context=None):
            fix_calls.append(("apply", context.phase, context.dataset_id))
            return provider.apply(dataset, context=context)

    monkeypatch.setattr(
        concat_mod, "get_dataset_fix_provider", lambda: TrackingProvider()
    )

    operation_calls = []

    class ConcatOperation:
        def call(self, inputs):
            operation_calls.append(("concat", dict(inputs)))
            return concat_mod.concat(
                **inputs,
                output_dir=output_dir.as_posix(),
            ).file_uris

    class UnexpectedSubsetOperation:
        def call(self, _inputs):
            pytest.fail("the fully pushed-down subset must be a pass-through")

    class RecordingProvenance:
        def __init__(self):
            self.steps = []

        def add_operator(self, step_id, _inputs, _collection, result):
            self.steps.append((step_id, result))

    workflow = Workflow(output_dir=tmp_path)
    workflow.operations = {
        "concat": ConcatOperation(),
        "subset": UnexpectedSubsetOperation(),
    }
    workflow.prov = RecordingProvenance()
    document = {
        "doc": "small decadal concat workflow",
        "inputs": {"datasets": sources},
        "outputs": {"output": "subset/output"},
        "steps": {
            "concat": {
                "run": "concat",
                "in": {"collection": "inputs/datasets", "dims": "realization"},
            },
            "subset": {
                "run": "subset",
                "in": {
                    "collection": "concat/output",
                    "time": "2000/2001",
                    "area": "10,-20,40,20",
                },
            },
        },
    }

    outputs = workflow._run(document)

    assert len(outputs) == 2
    assert outputs == workflow.prov.steps[-1][1]
    assert [step for step, _result in workflow.prov.steps] == ["concat", "subset"]
    assert len(operation_calls) == 1
    assert operation_calls[0][1]["time"] == "2000/2001"
    assert operation_calls[0][1]["area"] == "10,-20,40,20"
    assert not list(tmp_path.glob("subset_*"))

    assert len(opened) == 4
    assert closed == opened
    assert sum("2000" in path for path in opened) == 2
    assert sum("2001" in path for path in opened) == 2
    assert sum(call[0] == "apply" for call in fix_calls) == 4
    assert any(call[0] == "prepare" for call in fix_calls)

    for year, path in zip((2000, 2001), outputs, strict=True):
        with xr.open_dataset(path) as dataset:
            assert dataset.sizes == {
                "realization": 2,
                "time": 12,
                "lat": 4,
                "lon": 4,
            }
            assert set(dataset.time.dt.year.values) == {year}
            assert dataset.realization.values.tolist() == [0, 1]
            assert dataset.realization.attrs == {"standard_name": "realization"}
            assert dataset.lat.min() >= -20
            assert dataset.lat.max() <= 20
            assert dataset.lon.min() >= 10
            assert dataset.lon.max() <= 40
            assert dataset.attrs["project_id"] == "CMIP6"
            assert dataset.attrs["dataset_id"].startswith("CMIP6.DCPP.")
