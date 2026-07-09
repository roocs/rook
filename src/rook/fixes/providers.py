"""Dataset fix provider adapters."""

from abc import ABC, abstractmethod

WOODPECKER_CMIP6_DECADAL_RECIPE_ID = "cmip6_decadal.full"


class DatasetFixProvider(ABC):
    """Base class for dataset fix providers."""

    name = "base"

    @abstractmethod
    def apply_decadal_fixes(self, ds_id, ds, *, output_dir=None):
        """Apply CMIP6-decadal fixes and return the dataset."""


class LegacyDatasetFixProvider(DatasetFixProvider):
    """Rook's legacy CMIP6-decadal fix provider."""

    name = "legacy"

    def apply_decadal_fixes(self, ds_id, ds, *, output_dir=None):
        from rook.utils.decadal_fixes import apply_decadal_fixes

        return apply_decadal_fixes(ds_id, ds, output_dir=output_dir)


class WoodpeckerDatasetFixProvider(DatasetFixProvider):
    """Woodpecker-backed CMIP6-decadal fix provider."""

    name = "woodpecker"

    def apply_decadal_fixes(self, ds_id, ds, *, output_dir=None):
        try:
            import woodpecker
        except ImportError as exc:
            raise ImportError(
                "Woodpecker is required to apply CMIP6-decadal fixes with the "
                "woodpecker backend. Install woodpecker and the "
                "woodpecker-cmip6-decadal plugin, or use the legacy backend."
            ) from exc

        recipe = woodpecker.recipe.get(WOODPECKER_CMIP6_DECADAL_RECIPE_ID)
        if woodpecker.recipe.check(ds, recipe):
            woodpecker.recipe.fix(ds, recipe, dry_run=False)
        return ds


DATASET_FIX_PROVIDERS = {
    LegacyDatasetFixProvider.name: LegacyDatasetFixProvider,
    WoodpeckerDatasetFixProvider.name: WoodpeckerDatasetFixProvider,
}


def get_dataset_fix_provider(name="legacy"):
    """Return a configured dataset fix provider."""
    provider = DATASET_FIX_PROVIDERS.get(name)
    if provider is None:
        allowed = ", ".join(sorted(DATASET_FIX_PROVIDERS))
        raise ValueError(
            f"Unsupported dataset fix provider: {name!r}. Use one of: {allowed}"
        )
    return provider()
