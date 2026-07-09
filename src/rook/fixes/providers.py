"""Dataset fix provider registry."""

from rook.fixes.base import DatasetFixProvider as DatasetFixProvider
from rook.fixes.base import FixContext as FixContext
from rook.fixes.base import FixProvider as FixProvider
from rook.fixes.legacy import LegacyDatasetFixProvider as LegacyDatasetFixProvider
from rook.fixes.woodpecker import (
    WOODPECKER_CMIP6_DECADAL_CALENDAR_FIX_ID as WOODPECKER_CMIP6_DECADAL_CALENDAR_FIX_ID,
)
from rook.fixes.woodpecker import (
    WOODPECKER_CMIP6_DECADAL_RECIPE_ID as WOODPECKER_CMIP6_DECADAL_RECIPE_ID,
)
from rook.fixes.woodpecker import (
    WoodpeckerDatasetFixProvider as WoodpeckerDatasetFixProvider,
)

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
