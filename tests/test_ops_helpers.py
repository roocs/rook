import rook.utils.ops.helpers as helpers


def test_open_dataset_applies_fixes(monkeypatch):
    calls = {"open": 0, "fix": 0}

    def fake_open(file_paths):
        calls["open"] += 1
        assert file_paths == ["a.nc"]
        return "DATASET"

    def fake_apply(ds_id, ds):
        calls["fix"] += 1
        assert ds_id == "project.dataset"
        assert ds == "DATASET"
        return "FIXED"

    monkeypatch.setattr(helpers, "open_xr_dataset", fake_open)
    monkeypatch.setattr(helpers, "apply_dataset_fixes", fake_apply)
    monkeypatch.setattr(helpers, "is_kerchunk_file", lambda _: False)

    result = helpers.open_dataset("project.dataset", ["a.nc"], apply_fixes=True)

    assert result == "FIXED"
    assert calls == {"open": 1, "fix": 1}


def test_open_dataset_skips_fixes_when_disabled(monkeypatch):
    calls = {"open": 0, "fix": 0}

    def fake_open(file_paths):
        calls["open"] += 1
        return "DATASET"

    def fake_apply(ds_id, ds):
        calls["fix"] += 1
        return "FIXED"

    monkeypatch.setattr(helpers, "open_xr_dataset", fake_open)
    monkeypatch.setattr(helpers, "apply_dataset_fixes", fake_apply)
    monkeypatch.setattr(helpers, "is_kerchunk_file", lambda _: False)

    result = helpers.open_dataset("project.dataset", ["a.nc"], apply_fixes=False)

    assert result == "DATASET"
    assert calls == {"open": 1, "fix": 0}


def test_open_dataset_skips_fixes_for_kerchunk(monkeypatch):
    calls = {"open": 0, "fix": 0}

    def fake_open(file_paths):
        calls["open"] += 1
        return "DATASET"

    def fake_apply(ds_id, ds):
        calls["fix"] += 1
        return "FIXED"

    monkeypatch.setattr(helpers, "open_xr_dataset", fake_open)
    monkeypatch.setattr(helpers, "apply_dataset_fixes", fake_apply)
    monkeypatch.setattr(helpers, "is_kerchunk_file", lambda _: True)

    result = helpers.open_dataset("kerchunk.json", ["a.nc"], apply_fixes=True)

    assert result == "DATASET"
    assert calls == {"open": 1, "fix": 0}
