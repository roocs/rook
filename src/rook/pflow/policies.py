"""Request decision policies."""

ORIGINAL_FILE_PROJECTS = frozenset({"c3s-ipcc-atlas"})
PROCESSING_REQUIRED_INPUTS = frozenset({"dims", "freq", "grid"})


def may_return_original_files(project, inputs):
    """Return whether catalog data may be returned without processing."""
    return requests_original_files(inputs) or project_returns_original_files(project)


def requests_original_files(inputs):
    """Return whether the caller explicitly requested original files."""
    return bool(inputs.get("original_files"))


def project_returns_original_files(project):
    """Return whether a project currently bypasses processing by policy."""
    return project in ORIGINAL_FILE_PROJECTS


def requires_processing(inputs):
    """Return whether the requested operation changes data and must run."""
    return has_processing_required_input(inputs)


def has_processing_required_input(inputs):
    """Return whether current request parameters imply changed output data.

    This preserves the existing operation detection rule while keeping the
    hard-coded parameter names out of the main decision flow.
    """
    return bool(PROCESSING_REQUIRED_INPUTS.intersection(inputs))
