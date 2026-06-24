from clisops.utils.file_utils import FileMapper

import rook.operator as operator_mod
from rook.operator import Operator


class RecordingOperator(Operator):
    prefix = "recording"

    def __init__(self, output_dir):
        super().__init__(output_dir)
        self.runner_inputs = None

    def _get_runner(self):
        def runner(inputs):
            self.runner_inputs = inputs
            return ["processed.nc"]

        return runner


def fail_director(*_args, **_kwargs):
    raise AssertionError("director should not be called")


def test_direct_file_collection_is_processed_without_director(tmp_path, monkeypatch):
    source = tmp_path / "source.nc"
    source.touch()
    operator = RecordingOperator(tmp_path)
    monkeypatch.setattr(operator_mod, "wrap_director", fail_director)

    output_uris = operator.call(
        {
            "collection": [source.as_posix()],
            "apply_fixes": True,
            "original_files": True,
            "pre_checked": True,
        }
    )

    assert output_uris == ["processed.nc"]
    assert "apply_fixes" not in operator.runner_inputs
    assert "original_files" not in operator.runner_inputs
    assert "pre_checked" not in operator.runner_inputs
    assert isinstance(operator.runner_inputs["collection"], FileMapper)
    assert operator.runner_inputs["output_dir"].startswith(tmp_path.as_posix())


def test_later_workflow_step_receives_previous_step_files(tmp_path, monkeypatch):
    first = tmp_path / "first.nc"
    second = tmp_path / "second.nc"
    first.touch()
    second.touch()
    operator = RecordingOperator(tmp_path)
    monkeypatch.setattr(operator_mod, "wrap_director", fail_director)

    output_uris = operator.call({"collection": [first.as_posix(), second.as_posix()]})

    assert output_uris == ["processed.nc"]
    assert isinstance(operator.runner_inputs["collection"], FileMapper)
