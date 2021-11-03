import logging

from pywps import FORMATS, ComplexOutput, Format, LiteralInput, Process
from pywps.app.Common import Metadata
from pywps.app.exceptions import ProcessError

from ..usage import WPSUsage, Downloads
from roocs_utils.parameter import time_parameter


LOGGER = logging.getLogger()


class Usage(Process):
    def __init__(self):
        inputs = [
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
                "wpsusage",
                "WPSUsage",
                abstract="OGC:WPS metrics collected from pywps database.",
                as_reference=True,
                supported_formats=[FORMATS.CSV],
            ),
            ComplexOutput(
                "downloads",
                "Downloads",
                abstract="Downloads collected from nginx log file.",
                as_reference=True,
                supported_formats=[FORMATS.CSV],
            ),
        ]

        super(Usage, self).__init__(
            self._handler,
            identifier="usage",
            title="Usage",
            abstract="Run usage collector.",
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
        response.update_status("Usage started.", 0)
        if "time" in request.inputs:
            time = request.inputs["time"][0].data
            time_start, time_end = time_parameter.TimeParameter(time).get_bounds()
        else:
            time = None
            time_start = time_end = None
        try:
            usage = WPSUsage()
            response.outputs["wpsusage"].file = usage.collect(
                time_start=time_start, time_end=time_end, outdir=self.workdir
            )
            response.update_status("WPSUsage completed.", 50)
            # TODO: improve downloads usage collection
            # usage = Downloads()
            # response.outputs["downloads"].file = usage.collect(
            #     time_start=time_start, time_end=time_end, outdir=self.workdir
            # )
            emtpy_csv = "remote_host_ip,ip_number,datetime,timezone,request_type,request,protocol,status_code,size,referer,user_agent"  # noqa
            response.outputs["downloads"].data = emtpy_csv
            response.update_status("Downloads usage completed.", 90)
        except Exception as e:
            raise ProcessError(f"{e}")
        return response
