import pytest

from rook.fixes.providers import (
    LegacyDatasetFixProvider,
    WoodpeckerDatasetFixProvider,
    get_dataset_fix_provider,
)


def test_get_dataset_fix_provider_returns_legacy_provider_by_default():
    provider = get_dataset_fix_provider()

    assert isinstance(provider, LegacyDatasetFixProvider)
    assert provider.name == "legacy"


def test_get_dataset_fix_provider_returns_woodpecker_provider():
    provider = get_dataset_fix_provider("woodpecker")

    assert isinstance(provider, WoodpeckerDatasetFixProvider)
    assert provider.name == "woodpecker"


def test_get_dataset_fix_provider_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported dataset fix provider"):
        get_dataset_fix_provider("unknown")
