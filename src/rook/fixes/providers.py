"""Dataset fix provider adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

WOODPECKER_CMIP6_DECADAL_RECIPE_ID = "cmip6_decadal.full"


@dataclass(frozen=True)
class FixContext:
    """Rook-side context passed to a fix provider."""

    dataset_id: str | None = None
    operation: str | None = None
    phase: str | None = None
    output_dir: str | None = None
    recipe_id: str | None = None


class FixProvider(ABC):
    """Base class for dataset fix providers."""

    name = "base"

    def prepare(self, ds, *, context=None):
        """Prepare a dataset before the main fix step."""
        return ds

    @abstractmethod
    def apply(self, ds, *, context=None):
        """Apply fixes and return the dataset."""

    def finalise(self, ds, *, context=None):
        """Finalise a dataset after the main fix step."""
        return ds


class LegacyDatasetFixProvider(FixProvider):
    """Rook's legacy CMIP6-decadal fix provider."""

    name = "legacy"

    def prepare(self, ds, *, context=None):
        from rook.utils.decadal_fixes import decadal_fix_calendar

        # TODO: decide whether this special CMIP6-decadal pre-concat calendar
        # preparation belongs in Woodpecker or remains a Rook operation hook.
        return decadal_fix_calendar(None, ds)

    def apply(self, ds, *, context=None):
        from rook.utils.decadal_fixes import apply_decadal_fixes

        context = context or FixContext()
        return apply_decadal_fixes(
            context.dataset_id,
            ds,
            output_dir=context.output_dir,
        )


class WoodpeckerDatasetFixProvider(FixProvider):
    """Woodpecker-backed CMIP6-decadal fix provider."""

    name = "woodpecker"

    def prepare(self, ds, *, context=None):
        from rook.utils.decadal_fixes import decadal_fix_calendar

        # TODO: decide whether this special CMIP6-decadal pre-concat calendar
        # preparation belongs in Woodpecker or remains a Rook operation hook.
        return decadal_fix_calendar(None, ds)

    def apply(self, ds, *, context=None):
        try:
            import woodpecker
        except ImportError as exc:
            raise ImportError(
                "Woodpecker is required to apply CMIP6-decadal fixes with the "
                "woodpecker backend. Install woodpecker and the "
                "woodpecker-cmip6-decadal plugin, or use the legacy backend."
            ) from exc

        context = context or FixContext()
        recipe_id = context.recipe_id or WOODPECKER_CMIP6_DECADAL_RECIPE_ID
        recipe = woodpecker.recipe.get(recipe_id)
        if woodpecker.recipe.check(ds, recipe):
            woodpecker.recipe.fix(ds, recipe, dry_run=False)
        return ds


DatasetFixProvider = FixProvider

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
