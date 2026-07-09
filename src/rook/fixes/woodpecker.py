"""Woodpecker-backed dataset fix provider."""

import importlib

from rook.fixes.base import FixContext, FixProvider

WOODPECKER_CMIP6_DECADAL_RECIPE_ID = "cmip6_decadal.full"
WOODPECKER_CMIP6_DECADAL_CALENDAR_FIX_ID = "cmip6_decadal.calendar_normalization"


class WoodpeckerDatasetFixProvider(FixProvider):
    """Woodpecker-backed CMIP6-decadal fix provider."""

    name = "woodpecker"
    dependency_names = ("woodpecker", "woodpecker_cmip6_decadal_plugin")
    unavailable_message = (
        "Woodpecker is required to apply fixes with the woodpecker backend. "
        "Install woodpecker and the woodpecker-cmip6-decadal plugin, or use "
        "the legacy backend."
    )

    @property
    def woodpecker(self):
        """Return the Woodpecker module after checking provider dependencies."""
        self.require_available()
        return importlib.import_module("woodpecker")

    def prepare(self, ds, *, context=None):
        # TODO: decide whether this special CMIP6-decadal pre-concat calendar
        # preparation remains an operation hook or should be represented by a
        # dedicated recipe/phase in Woodpecker.
        self.woodpecker.fix(
            ds,
            fixes=WOODPECKER_CMIP6_DECADAL_CALENDAR_FIX_ID,
            dry_run=False,
        )
        return ds

    def apply(self, ds, *, context=None):
        context = context or FixContext()
        woodpecker = self.woodpecker
        recipe_id = context.recipe_id or WOODPECKER_CMIP6_DECADAL_RECIPE_ID
        recipe = woodpecker.recipe.get(recipe_id)
        if woodpecker.recipe.check(ds, recipe):
            woodpecker.recipe.fix(ds, recipe, dry_run=False)
        return ds
