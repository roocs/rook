import pytest
import xarray as xr

from rook.fixes.providers import (
    FixContext,
    FixProvider,
    LegacyDatasetFixProvider,
    WOODPECKER_ATLAS_RECIPE_ID,
    WOODPECKER_CMIP6_DECADAL_CALENDAR_FIX_ID,
    WOODPECKER_CMIP6_DECADAL_RECIPE_ID,
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
    assert provider.missing_dependencies() == ["missing_dependency"]
    with pytest.raises(
        ImportError,
        match=r"test provider is unavailable Missing: missing_dependency\.",
    ):
        provider.require_available()


def test_legacy_provider_prepares_decadal_concat_dataset(monkeypatch):
    from rook.fixes.legacy import decadal as legacy_decadal

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


def test_legacy_provider_applies_atlas_fixes(monkeypatch):
    from rook.fixes.legacy import atlas as legacy_atlas

    calls = []
    source = xr.Dataset(attrs={"source": "input"})

    def fake_atlas(ds_id, ds):
        calls.append((ds_id, ds.attrs["source"]))
        return ds.assign_attrs(project_id="c3s-ipcc-atlas")

    monkeypatch.setattr(legacy_atlas, "apply_atlas_fixes", fake_atlas)

    result = LegacyDatasetFixProvider().apply(
        source,
        context=FixContext(dataset_id="c3s-ipcc-atlas.tnn.CMIP6.historical.mon"),
    )

    assert result.attrs["project_id"] == "c3s-ipcc-atlas"
    assert calls == [("c3s-ipcc-atlas.tnn.CMIP6.historical.mon", "input")]


def test_legacy_provider_leaves_unknown_dataset_unchanged():
    source = xr.Dataset(attrs={"source": "input"})

    result = LegacyDatasetFixProvider().apply(
        source,
        context=FixContext(dataset_id="unknown.project.dataset"),
    )

    assert result is source


def test_get_dataset_fix_provider_returns_woodpecker_provider():
    provider = get_dataset_fix_provider("woodpecker")

    assert isinstance(provider, WoodpeckerDatasetFixProvider)
    assert provider.name == "woodpecker"


def test_woodpecker_provider_prepares_decadal_concat_dataset(monkeypatch):
    calls = []
    source = xr.Dataset(attrs={"source": "input"})

    class FakeWoodpecker:
        @staticmethod
        def apply(ds, *, fixes=None, dry_run=True):
            calls.append(("apply", ds.attrs["source"], fixes, dry_run))

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
        ("apply", "input", WOODPECKER_CMIP6_DECADAL_CALENDAR_FIX_ID, False),
    ]


def test_woodpecker_provider_applies_decadal_recipe_without_check(monkeypatch):
    calls = []
    source = xr.Dataset(attrs={"source": "input"})

    class FakeRecipe:
        @staticmethod
        def get(recipe_id):
            calls.append(("get", recipe_id))
            return {"id": recipe_id}

        @staticmethod
        def check(ds, recipe):
            raise AssertionError("Rook should call Woodpecker apply directly")

        @staticmethod
        def apply(ds, recipe, dry_run=True):
            calls.append(("apply", recipe["id"], ds.attrs["source"], dry_run))

    class FakeWoodpecker:
        recipe = FakeRecipe

    monkeypatch.setattr(
        WoodpeckerDatasetFixProvider, "require_available", lambda self: None
    )
    monkeypatch.setattr("importlib.import_module", lambda name: FakeWoodpecker)

    result = WoodpeckerDatasetFixProvider().apply(
        source,
        context=FixContext(dataset_id="c3s-cmip6-decadal.example.dataset"),
    )

    assert result is source
    assert calls == [
        ("get", WOODPECKER_CMIP6_DECADAL_RECIPE_ID),
        ("apply", WOODPECKER_CMIP6_DECADAL_RECIPE_ID, "input", False),
    ]


def test_woodpecker_provider_applies_atlas_recipe(monkeypatch):
    calls = []
    source = xr.Dataset(attrs={"source": "input"})

    class FakeRecipe:
        @staticmethod
        def get(recipe_id):
            calls.append(("get", recipe_id))
            return {"id": recipe_id}

        @staticmethod
        def apply(ds, recipe, dry_run=True):
            calls.append(
                (
                    "apply",
                    recipe["id"],
                    ds.attrs["dataset_id"],
                    ds.attrs["source_name"],
                    dry_run,
                )
            )
            ds.attrs["project_id"] = "c3s-ipcc-atlas"

    class FakeWoodpecker:
        recipe = FakeRecipe

    monkeypatch.setattr(
        WoodpeckerDatasetFixProvider, "require_available", lambda self: None
    )
    monkeypatch.setattr("importlib.import_module", lambda name: FakeWoodpecker)

    result = WoodpeckerDatasetFixProvider().apply(
        source,
        context=FixContext(dataset_id="c3s-ipcc-atlas.tnn.CMIP6.historical.mon"),
    )

    assert result is source
    assert result.attrs == {"source": "input", "project_id": "c3s-ipcc-atlas"}
    assert calls == [
        ("get", WOODPECKER_ATLAS_RECIPE_ID),
        (
            "apply",
            WOODPECKER_ATLAS_RECIPE_ID,
            "c3s-ipcc-atlas.tnn.CMIP6.historical.mon",
            "c3s-ipcc-atlas.tnn.CMIP6.historical.mon.nc",
            False,
        ),
    ]


def test_woodpecker_provider_leaves_unknown_dataset_unchanged(monkeypatch):
    source = xr.Dataset(attrs={"source": "input"})

    monkeypatch.setattr(
        WoodpeckerDatasetFixProvider,
        "woodpecker",
        property(lambda self: pytest.fail("Woodpecker should not be loaded")),
    )

    result = WoodpeckerDatasetFixProvider().apply(
        source,
        context=FixContext(dataset_id="unknown.project.dataset"),
    )

    assert result is source


def test_get_dataset_fix_provider_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported dataset fix provider"):
        get_dataset_fix_provider("unknown")
