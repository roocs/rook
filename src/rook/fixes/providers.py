"""Dataset fix provider registry."""

from rook.fixes.base import DatasetFixProvider, FixContext, FixProvider
from rook.fixes.legacy import LegacyDatasetFixProvider
from rook.fixes.woodpecker import (
    WOODPECKER_CMIP6_DECADAL_CALENDAR_FIX_ID,
    WOODPECKER_CMIP6_DECADAL_RECIPE_ID,
    WoodpeckerDatasetFixProvider,
)

__all__ = [
    "WOODPECKER_CMIP6_DECADAL_CALENDAR_FIX_ID",
    "WOODPECKER_CMIP6_DECADAL_RECIPE_ID",
    "DatasetFixProvider",
    "FixContext",
    "FixProvider",
    "LegacyDatasetFixProvider",
    "WoodpeckerDatasetFixProvider",
    "get_dataset_fix_provider",
]

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
