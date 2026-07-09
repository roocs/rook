import pytest
import xarray as xr

from rook.fixes.providers import (
    FixContext,
    FixProvider,
    LegacyDatasetFixProvider,
    WOODPECKER_CMIP6_DECADAL_CALENDAR_FIX_ID,
    WoodpeckerDatasetFixProvider,
    get_dataset_fix_provider,
)


def test_get_dataset_fix_provider_returns_legacy_provider_by_default():
    provider = get_dataset_fix_provider()

    assert isinstance(provider, LegacyDatasetFixProvider)
    assert provider.name == "legacy"


def test_get_dataset_fix_provider_uses_configured_default(monkeypatch):
    monkeypatch.setattr("rook.fixes.providers.get_fix_backend", lambda: "woodpecker")

    provider = get_dataset_fix_provider()

    assert isinstance(provider, WoodpeckerDatasetFixProvider)
    assert provider.name == "woodpecker"


def test_fix_provider_finalise_is_noop():
    class TestProvider(FixProvider):
        def apply(self, ds, *, context=None):
            return ds

    source = xr.Dataset(attrs={"source": "input"})

    result = TestProvider().finalise(source, context=FixContext(operation="concat"))

    assert result is source


def test_fix_provider_without_dependencies_is_available():
    class TestProvider(FixProvider):
        def apply(self, ds, *, context=None):
            return ds

    assert TestProvider().available()


def test_fix_provider_requires_declared_dependencies(monkeypatch):
    class TestProvider(FixProvider):
        dependency_names = ("available_dependency", "missing_dependency")
        unavailable_message = "test provider is unavailable"

        def apply(self, ds, *, context=None):
            return ds

    def fake_find_spec(name):
        if name == "available_dependency":
            return object()
        return None

    provider = TestProvider()
    monkeypatch.setattr("importlib.util.find_spec", fake_find_spec)

    assert not provider.available()
    with pytest.raises(ImportError, match="test provider is unavailable"):
        provider.require_available()


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
    calls = []
    source = xr.Dataset(attrs={"source": "input"})

    class FakeWoodpecker:
        @staticmethod
        def fix(ds, *, fixes=None, dry_run=True):
            calls.append(("fix", ds.attrs["source"], fixes, dry_run))

    monkeypatch.setattr(
        WoodpeckerDatasetFixProvider, "require_available", lambda self: None
    )
    monkeypatch.setattr("importlib.import_module", lambda name: FakeWoodpecker)

    result = WoodpeckerDatasetFixProvider().prepare(
        source,
        context=FixContext(operation="concat", phase="prepare"),
    )

    assert result is source
    assert calls == [
        ("fix", "input", WOODPECKER_CMIP6_DECADAL_CALENDAR_FIX_ID, False),
    ]


def test_get_dataset_fix_provider_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported dataset fix provider"):
        get_dataset_fix_provider("unknown")
