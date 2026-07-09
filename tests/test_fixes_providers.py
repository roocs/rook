import pytest
import xarray as xr

from rook.fixes.providers import (
    FixContext,
    FixProvider,
    LegacyDatasetFixProvider,
    WoodpeckerDatasetFixProvider,
    get_dataset_fix_provider,
)


def test_get_dataset_fix_provider_returns_legacy_provider_by_default():
    provider = get_dataset_fix_provider()

    assert isinstance(provider, LegacyDatasetFixProvider)
    assert provider.name == "legacy"


def test_fix_provider_finalise_is_noop():
    class TestProvider(FixProvider):
        def apply(self, ds, *, context=None):
            return ds

    source = xr.Dataset(attrs={"source": "input"})

    result = TestProvider().finalise(source, context=FixContext(operation="concat"))

    assert result is source


def test_legacy_provider_prepares_decadal_concat_dataset(monkeypatch):
    from rook.fixes import legacy_decadal

    calls = []
    source = xr.Dataset(attrs={"source": "input"})

    def fake_calendar(ds_id, ds):
        calls.append((ds_id, ds.attrs["source"]))
        return ds

    monkeypatch.setattr(legacy_decadal, "decadal_fix_calendar", fake_calendar)

    result = LegacyDatasetFixProvider().prepare(
        source,
        context=FixContext(operation="concat", phase="prepare"),
    )

    assert result is source
    assert calls == [(None, "input")]


def test_get_dataset_fix_provider_returns_woodpecker_provider():
    provider = get_dataset_fix_provider("woodpecker")

    assert isinstance(provider, WoodpeckerDatasetFixProvider)
    assert provider.name == "woodpecker"


def test_woodpecker_provider_prepares_decadal_concat_dataset(monkeypatch):
    from rook.fixes import legacy_decadal

    calls = []
    source = xr.Dataset(attrs={"source": "input"})

    def fake_calendar(ds_id, ds):
        calls.append((ds_id, ds.attrs["source"]))
        return ds

    monkeypatch.setattr(legacy_decadal, "decadal_fix_calendar", fake_calendar)

    result = WoodpeckerDatasetFixProvider().prepare(
        source,
        context=FixContext(operation="concat", phase="prepare"),
    )

    assert result is source
    assert calls == [(None, "input")]


def test_get_dataset_fix_provider_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported dataset fix provider"):
        get_dataset_fix_provider("unknown")
