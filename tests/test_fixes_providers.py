import pytest
import xarray as xr

from rook.fixes.providers import (
    LegacyDatasetFixProvider,
    WoodpeckerDatasetFixProvider,
    get_dataset_fix_provider,
)


def test_get_dataset_fix_provider_returns_legacy_provider_by_default():
    provider = get_dataset_fix_provider()

    assert isinstance(provider, LegacyDatasetFixProvider)
    assert provider.name == "legacy"


def test_legacy_provider_prepares_decadal_concat_dataset(monkeypatch):
    from rook.utils import decadal_fixes

    calls = []
    source = xr.Dataset(attrs={"source": "input"})

    def fake_calendar(ds_id, ds):
        calls.append((ds_id, ds.attrs["source"]))
        return ds

    monkeypatch.setattr(decadal_fixes, "decadal_fix_calendar", fake_calendar)

    result = LegacyDatasetFixProvider().prepare_decadal_concat_dataset(source)

    assert result is source
    assert calls == [(None, "input")]


def test_get_dataset_fix_provider_returns_woodpecker_provider():
    provider = get_dataset_fix_provider("woodpecker")

    assert isinstance(provider, WoodpeckerDatasetFixProvider)
    assert provider.name == "woodpecker"


def test_woodpecker_provider_prepares_decadal_concat_dataset(monkeypatch):
    from rook.utils import decadal_fixes

    calls = []
    source = xr.Dataset(attrs={"source": "input"})

    def fake_calendar(ds_id, ds):
        calls.append((ds_id, ds.attrs["source"]))
        return ds

    monkeypatch.setattr(decadal_fixes, "decadal_fix_calendar", fake_calendar)

    result = WoodpeckerDatasetFixProvider().prepare_decadal_concat_dataset(source)

    assert result is source
    assert calls == [(None, "input")]


def test_get_dataset_fix_provider_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported dataset fix provider"):
        get_dataset_fix_provider("unknown")
