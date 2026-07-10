"""Woodpecker-backed dataset fix provider."""

import importlib

from rook.fixes.providers.base import FixContext, FixProvider

WOODPECKER_CMIP6_DECADAL_RECIPE_ID = "cmip6_decadal.full"
WOODPECKER_CMIP6_DECADAL_CALENDAR_FIX_ID = "cmip6_decadal.calendar_normalization"
WOODPECKER_ATLAS_RECIPE_ID = "atlas.basic"


class WoodpeckerDatasetFixProvider(FixProvider):
    """Woodpecker-backed dataset fix provider."""

    name = "woodpecker"
    dependency_names = (
        "woodpecker",
        "woodpecker_atlas_plugin",
        "woodpecker_cmip6_decadal_plugin",
    )
    unavailable_message = (
        "Woodpecker is required to apply fixes with the woodpecker backend. "
        "Install woodpecker, the woodpecker-atlas plugin, and the "
        "woodpecker-cmip6-decadal plugin, or use the legacy backend."
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
        self.woodpecker.apply(
            ds,
            fixes=WOODPECKER_CMIP6_DECADAL_CALENDAR_FIX_ID,
            dry_run=False,
        )
        return ds

    def apply(self, ds, *, context=None):
        context = context or FixContext()
        dataset_id = context.dataset_id or ""

        if dataset_id.startswith(("c3s-ipcc-atlas", "c3s-cica-atlas")):
            recipe_id = context.recipe_id or WOODPECKER_ATLAS_RECIPE_ID
            return self._apply_atlas_recipe(ds, dataset_id, recipe_id)

        if not dataset_id.startswith("c3s-cmip6-decadal"):
            return ds

        woodpecker = self.woodpecker
        recipe_id = context.recipe_id or WOODPECKER_CMIP6_DECADAL_RECIPE_ID
        recipe = woodpecker.recipe.get(recipe_id)
        woodpecker.recipe.apply(ds, recipe, dry_run=False)
        return ds

    def _apply_atlas_recipe(self, ds, dataset_id, recipe_id):
        woodpecker = self.woodpecker
        previous_dataset_id = ds.attrs.get("dataset_id")
        previous_source_name = ds.attrs.get("source_name")
        ds.attrs["dataset_id"] = dataset_id
        ds.attrs["source_name"] = f"{dataset_id}.nc"

        try:
            recipe = woodpecker.recipe.get(recipe_id)
            woodpecker.recipe.apply(ds, recipe, dry_run=False)
        finally:
            if previous_dataset_id is None:
                ds.attrs.pop("dataset_id", None)
            else:
                ds.attrs["dataset_id"] = previous_dataset_id

            if previous_source_name is None:
                ds.attrs.pop("source_name", None)
            else:
                ds.attrs["source_name"] = previous_source_name

        return ds
