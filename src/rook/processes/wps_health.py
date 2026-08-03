"""Health-check process."""

from pywps import LiteralOutput, Process
from pywps.app.Common import Metadata


class Health(Process):
    """Report that Rook can execute a WPS process."""

    def __init__(self):
        outputs = [
            LiteralOutput(
                "status",
                "Status",
                abstract="Rook health status.",
                data_type="string",
            )
        ]

        super().__init__(
            self._handler,
            identifier="health",
            title="Health",
            abstract="Check whether Rook can execute a WPS process.",
            metadata=[Metadata("ROOK", "https://github.com/roocs/rook")],
            version="1.0",
            inputs=[],
            outputs=outputs,
            store_supported=False,
            status_supported=False,
        )

    def _handler(self, _request, response):
        response.outputs["status"].data = "ok"
        return response
