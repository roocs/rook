"""Synchronous operational status process."""

import json

from pywps import FORMATS, ComplexOutput, Format, Process
from pywps.app.Common import Metadata

from rook.status import collect_status, render_html

HTML_FORMAT = Format("text/html", extension=".html")


class Status(Process):
    """Return the current Rook operational status synchronously.

    The ``json`` output is a versioned document intended for monitoring. The
    ``html`` output renders that same document as a small human-readable page.
    Individual check failures are represented in the report and do not prevent
    the remaining checks from being returned.
    """

    def __init__(self):
        outputs = [
            ComplexOutput(
                "json",
                "JSON status report",
                abstract="Versioned Rook operational status report.",
                supported_formats=[FORMATS.JSON],
            ),
            ComplexOutput(
                "html",
                "HTML status overview",
                abstract="Human-readable Rook operational status overview.",
                supported_formats=[HTML_FORMAT],
            ),
        ]

        super().__init__(
            self._handler,
            identifier="status",
            title="Status",
            abstract="Report Rook service, process, server, and storage status.",
            metadata=[Metadata("ROOK", "https://github.com/roocs/rook")],
            version="1.0",
            inputs=[],
            outputs=outputs,
            store_supported=False,
            status_supported=False,
        )

    def _handler(self, _request, response):
        report = collect_status()
        response.outputs["json"].data = json.dumps(report, sort_keys=True)
        response.outputs["html"].data = render_html(report)
        return response
