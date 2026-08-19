"""Woodpecker-backed dataset fix provider."""

import importlib
from functools import cached_property

from rook.diagnostics import memory_checkpoint
from rook.fixes.providers.base import (
    ATLAS_DATASET_PREFIXES,
    CMIP6_DECADAL_DATASET_PREFIX,
    FixContext,
    FixProvider,
)

WOODPECKER_CMIP6_DECADAL_RECIPE_ID = "c3s.cmip6_decadal"
WOODPECKER_ATLAS_RECIPE_ID = "c3s.atlas"
WOODPECKER_PREPARE_PHASE = "prepare"
WOODPECKER_APPLY_PHASE = "apply"


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
        "Install roocs-woodpecker, roocs-woodpecker-atlas-plugin, and "
        "roocs-woodpecker-cmip6-decadal-plugin, or use the legacy backend."
    )

    @cached_property
    def woodpecker(self):
        """Return the Woodpecker module after checking provider dependencies."""
        self.require_available()
        return importlib.import_module("woodpecker")

    def prepare(self, ds, *, context=None):
        context = context or FixContext()
        dataset_id = context.dataset_id or ""
        if dataset_id.startswith(CMIP6_DECADAL_DATASET_PREFIX):
            return self._apply_decadal_recipe(
                ds,
                dataset_id=dataset_id,
                recipe_id=context.recipe_id or WOODPECKER_CMIP6_DECADAL_RECIPE_ID,
                phase=context.phase or WOODPECKER_PREPARE_PHASE,
            )
        return self._apply_recipe(
            ds,
            recipe_id=context.recipe_id or WOODPECKER_CMIP6_DECADAL_RECIPE_ID,
            phase=context.phase or WOODPECKER_PREPARE_PHASE,
        )

    def apply(self, ds, *, context=None):
        context = context or FixContext()
        dataset_id = context.dataset_id or ""

        if dataset_id.startswith(ATLAS_DATASET_PREFIXES):
            return self._apply_atlas_recipe(
                ds,
                dataset_id=dataset_id,
                recipe_id=context.recipe_id or WOODPECKER_ATLAS_RECIPE_ID,
            )

        if dataset_id.startswith(CMIP6_DECADAL_DATASET_PREFIX):
            return self._apply_decadal_recipe(
                ds,
                dataset_id=dataset_id,
                recipe_id=context.recipe_id or WOODPECKER_CMIP6_DECADAL_RECIPE_ID,
                phase=context.phase or WOODPECKER_APPLY_PHASE,
            )

        return ds

    def _apply_decadal_recipe(self, ds, *, dataset_id, recipe_id, phase):
        """Expose the catalog identity while Woodpecker matches decadal fixes."""
        previous_source_name = ds.attrs.get("source_name")
        ds.attrs["source_name"] = f"{dataset_id}.nc"
        try:
            return self._apply_recipe(
                ds,
                recipe_id=recipe_id,
                phase=phase,
                dataset_id=dataset_id,
            )
        finally:
            if previous_source_name is None:
                ds.attrs.pop("source_name", None)
            else:
                ds.attrs["source_name"] = previous_source_name

    def _apply_atlas_recipe(self, ds, *, dataset_id, recipe_id):
        previous_dataset_id = ds.attrs.get("dataset_id")
        previous_source_name = ds.attrs.get("source_name")
        # TODO: clean up this temporary attribute workaround when revisiting
        # c3s-atlas fix handling in Woodpecker.
        ds.attrs["dataset_id"] = dataset_id
        ds.attrs["source_name"] = f"{dataset_id}.nc"

        try:
            self._apply_recipe(
                ds,
                recipe_id=recipe_id,
                phase=WOODPECKER_APPLY_PHASE,
                dataset_id=dataset_id,
            )
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

    def _apply_recipe(self, ds, *, recipe_id, phase=None, dataset_id=None):
        recipe = self.woodpecker.recipe.get(recipe_id)
        result = self.woodpecker.recipe.apply(
            ds,
            recipe,
            phase=phase,
            dry_run=False,
        )
        stats = getattr(result, "stats", None) or {}
        identity = (
            dataset_id
            or ds.attrs.get("dataset_id")
            or ds.attrs.get("source_name")
            or "unknown"
        )
        details = (
            f"dataset={identity} recipe={recipe_id} phase={phase} "
            f"attempted={stats.get('attempted', 'unknown')} "
            f"changed={stats.get('changed', 'unknown')}"
        )
        memory_checkpoint("Woodpecker fixes applied", details)
        return ds
