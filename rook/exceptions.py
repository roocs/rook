class WorkflowValidationError(Exception):
    pass


class InvalidCollection(Exception):
    def __init__(self):
        self.message = (
            "Some or all of the requested collection are not in the list "
            "of available data."
        )
        super().__init__(self.message)
