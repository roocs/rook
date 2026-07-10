"""Legacy Rook dataset fix provider."""

from rook.fixes.base import FixContext, FixProvider


class LegacyDatasetFixProvider(FixProvider):
    """Rook's legacy dataset fix provider."""

    name = "legacy"

    def prepare(self, ds, *, context=None):
        from rook.fixes.legacy_decadal import decadal_fix_calendar

        # TODO: decide whether this special CMIP6-decadal pre-concat calendar
        # preparation belongs in Woodpecker or remains a Rook operation hook.
        return decadal_fix_calendar(None, ds)

    def apply(self, ds, *, context=None):
        context = context or FixContext()
        dataset_id = context.dataset_id or ""

        if dataset_id.startswith(("c3s-ipcc-atlas", "c3s-cica-atlas")):
            from rook.fixes.legacy_atlas import apply_atlas_fixes

            return apply_atlas_fixes(dataset_id, ds)

        if dataset_id.startswith("c3s-cmip6-decadal"):
            from rook.fixes.legacy_decadal import apply_decadal_fixes

            return apply_decadal_fixes(
                dataset_id,
                ds,
                output_dir=context.output_dir,
            )

        return ds
