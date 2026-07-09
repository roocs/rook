"""Dataset fix provider adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import importlib
import importlib.util

WOODPECKER_CMIP6_DECADAL_RECIPE_ID = "cmip6_decadal.full"
WOODPECKER_CMIP6_DECADAL_CALENDAR_FIX_ID = "cmip6_decadal.calendar_normalization"


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
    dependency_names = ()
    unavailable_message = "The selected fix provider has missing dependencies."

    def available(self):
        """Return whether the provider dependencies are importable."""
        return all(
            importlib.util.find_spec(dependency_name) is not None
            for dependency_name in self.dependency_names
        )

    def require_available(self):
        """Raise a clear error when provider dependencies are missing."""
        if not self.available():
            raise ImportError(self.unavailable_message)

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
        from rook.fixes.legacy_decadal import decadal_fix_calendar

        # TODO: decide whether this special CMIP6-decadal pre-concat calendar
        # preparation belongs in Woodpecker or remains a Rook operation hook.
        return decadal_fix_calendar(None, ds)

    def apply(self, ds, *, context=None):
        from rook.fixes.legacy_decadal import apply_decadal_fixes

        context = context or FixContext()
        return apply_decadal_fixes(
            context.dataset_id,
            ds,
            output_dir=context.output_dir,
        )


class WoodpeckerDatasetFixProvider(FixProvider):
    """Woodpecker-backed CMIP6-decadal fix provider."""

    name = "woodpecker"
    dependency_names = ("woodpecker", "woodpecker_cmip6_decadal_plugin")
    unavailable_message = (
        "Woodpecker is required to apply fixes with the woodpecker backend. "
        "Install woodpecker and the woodpecker-cmip6-decadal plugin, or use "
        "the legacy backend."
    )

    def prepare(self, ds, *, context=None):
        # TODO: decide whether this special CMIP6-decadal pre-concat calendar
        # preparation remains an operation hook or should be represented by a
        # dedicated recipe/phase in Woodpecker.
        self.require_available()
        woodpecker = importlib.import_module("woodpecker")
        woodpecker.fix(
            ds,
            fixes=WOODPECKER_CMIP6_DECADAL_CALENDAR_FIX_ID,
            dry_run=False,
        )
        return ds

    def apply(self, ds, *, context=None):
        self.require_available()
        woodpecker = importlib.import_module("woodpecker")

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
