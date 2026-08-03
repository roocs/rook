class WorkflowValidationError(Exception):
    pass


class HealthCheckError(RuntimeError):
    """Raised when an operational health check fails."""
