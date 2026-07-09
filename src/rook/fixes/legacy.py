"""Legacy Rook dataset fix provider."""

from rook.fixes.base import FixContext, FixProvider


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
