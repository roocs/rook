import logging

from pywps import FORMATS, ComplexOutput, LiteralInput, Process
from pywps.app.Common import Metadata
from pywps.app.exceptions import ProcessError

from ..usage import Downloads as Downloads_
from roocs_utils.parameter import time_parameter


LOGGER = logging.getLogger()

EMPTY_CSV = """\
remote_host_ip,ip_number,datetime,timezone,request_type,request,protocol,status_code,size,referer,user_agent
127.0.0.1,1000000000,2021-01-01 12:00:00,+0200,GET,dummy.nc,HTTP/1.1,200,1000000,-,python
"""  # noqa


class Downloads(Process):
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
                "output",
                "Downloads",
                abstract="Downloads collected from nginx log file.",
                as_reference=True,
                supported_formats=[FORMATS.CSV],
            ),
        ]

        super(Downloads, self).__init__(
            self._handler,
            identifier="downloads",
            title="Usage",
            abstract="Run downloads collector.",
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
        response.update_status("Download collectior started.", 0)
        if "time" in request.inputs:
            time = request.inputs["time"][0].data
            time_start, time_end = time_parameter.TimeParameter(time).get_bounds()
        else:
            time = None
            time_start = time_end = None
        # downloads
        try:
            collector = Downloads_()
            downloads_csv = collector.collect(
                time_start=time_start, time_end=time_end, outdir=self.workdir
            )
            response.outputs["output"].file = downloads_csv
        except Exception:
            LOGGER.exception("downloads collection failed")
            response.outputs["output"].data = EMPTY_CSV
        finally:
            response.update_status("Downloads usage completed.", 90)

        return response
