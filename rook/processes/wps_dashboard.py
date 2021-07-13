import logging

from pywps import FORMATS, ComplexOutput, Format, LiteralInput, Process
from pywps.app.Common import Metadata
from pywps.app.exceptions import ProcessError

from ..usage import Combine
from ..dashboard import Dashboard
from roocs_utils.parameter import time_parameter


LOGGER = logging.getLogger()


class DashboardProcess(Process):
    def __init__(self):
        inputs = [
            LiteralInput(
                "site",
                "Compute Site",
                abstract="The name of the compute site" "Example: cds",
                data_type="string",
                min_occurs=1,
                max_occurs=1,
                default="local",
                allowed_values=["local", "ceda", "dkrz", "all"],
            ),
            LiteralInput(
                "time",
                "Time Period",
                abstract="The time period for usage collection seperated by /"
                "Example: 2021-04-01/2021-04-30",
                data_type="string",
                min_occurs=0,
                max_occurs=1,
            ),
        ]
        outputs = [
            ComplexOutput(
                "dashboard",
                "Dashboard",
                abstract="Dashboard of OGC:WPS metrics.",
                as_reference=True,
                supported_formats=[FORMATS.TEXT],
            ),
        ]

        super(DashboardProcess, self).__init__(
            self._handler,
            identifier="dashboard",
            title="Dashboard",
            abstract="Run dashboard.",
            metadata=[
                Metadata("ROOK", "https://github.com/roocs/rook"),
            ],
            version="0.1",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True,
        )

    def _handler(self, request, response):
        response.update_status("Dashboard started.", 0)
        if "time" in request.inputs:
            time = request.inputs["time"][0].data
            time_start, time_end = time_parameter.TimeParameter(time).tuple
        else:
            time = None
            time_start = time_end = None
        try:
            usage = Combine(site=request.inputs["site"][0].data)
            fusage, fdownloads = usage.collect(
                time_start=time_start, time_end=time_end, outdir=self.workdir
            )
            response.update_status("Combine completed.", 80)
            dashboard = Dashboard(output_dir=self.workdir)
            dashboard.load(url=fusage, filter="orchestrate")
            dashboard.load_downloads(url=fdownloads)
            response.outputs["dashboard"].file = dashboard.write()
            response.update_status("Dashboard completed.", 90)
        except Exception as e:
            raise ProcessError(f"{e}")
        return response
