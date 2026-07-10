"""Dataset fix provider registry."""

from rook.config import get_fix_backend
from rook.fixes.providers.base import DatasetFixProvider as DatasetFixProvider
from rook.fixes.providers.base import FixContext as FixContext
from rook.fixes.providers.base import FixProvider as FixProvider
from rook.fixes.providers.legacy import (
    LegacyDatasetFixProvider as LegacyDatasetFixProvider,
)
from rook.fixes.providers.woodpecker import (
    WOODPECKER_CMIP6_DECADAL_RECIPE_ID as WOODPECKER_CMIP6_DECADAL_RECIPE_ID,
)
from rook.fixes.providers.woodpecker import (
    WOODPECKER_ATLAS_RECIPE_ID as WOODPECKER_ATLAS_RECIPE_ID,
)
from rook.fixes.providers.woodpecker import (
    WoodpeckerDatasetFixProvider as WoodpeckerDatasetFixProvider,
)

DATASET_FIX_PROVIDERS = {
    LegacyDatasetFixProvider.name: LegacyDatasetFixProvider,
    WoodpeckerDatasetFixProvider.name: WoodpeckerDatasetFixProvider,
}


def get_dataset_fix_provider(name=None):
    """Return a configured dataset fix provider."""
    if name is None:
        name = get_fix_backend()

    provider = DATASET_FIX_PROVIDERS.get(name)
    if provider is None:
        allowed = ", ".join(sorted(DATASET_FIX_PROVIDERS))
        raise ValueError(
            f"Unsupported dataset fix provider: {name!r}. Use one of: {allowed}"
        )
    return provider()
