import logging
import os

from pywps import FORMATS, ComplexOutput, Format, LiteralInput, Process
from pywps.app.Common import Metadata
from pywps.app.exceptions import ProcessError
from pywps.inout.outputs import MetaFile, MetaLink4

from ..director import wrap_director
from ..utils.input_utils import parse_wps_input
from ..utils.metalink_utils import build_metalink
from ..utils.response_utils import populate_response
from ..utils.concat_utils import run_concat

LOGGER = logging.getLogger()


class Concat(Process):
    def __init__(self):
        inputs = [
            LiteralInput(
                "collections",
                "Collections",
                abstract="A list of dataset identifiers. "
                "Example: c3s-cmip5.output1.ICHEC.EC-EARTH.historical.day.atmos.day.r1i1p1.tas.latest",
                data_type="string",
                min_occurs=1,
                max_occurs=10,
            ),
            LiteralInput(
                "pre_checked",
                "Pre-Checked",
                data_type="boolean",
                abstract="Use checked data only.",
                default="0",
                min_occurs=1,
                max_occurs=1,
            ),
            LiteralInput(
                "apply_fixes",
                "Apply Fixes",
                data_type="boolean",
                abstract="Apply fixes to datasets.",
                default="1",
                min_occurs=1,
                max_occurs=1,
            ),
        ]
        outputs = [
            ComplexOutput(
                "output",
                "METALINK v4 output",
                abstract="Metalink v4 document with references to NetCDF files.",
                as_reference=True,
                supported_formats=[FORMATS.META4],
            ),
            ComplexOutput(
                "prov",
                "Provenance",
                abstract="Provenance document using W3C standard.",
                as_reference=True,
                supported_formats=[FORMATS.JSON],
            ),
            ComplexOutput(
                "prov_plot",
                "Provenance Diagram",
                abstract="Provenance document as diagram.",
                as_reference=True,
                supported_formats=[
                    Format("image/png", extension=".png", encoding="base64")
                ],
            ),
        ]

        super(Concat, self).__init__(
            self._handler,
            identifier="concat",
            title="Concat",
            abstract="Run concat on climate model data.",
            metadata=[
                Metadata("DAOPS", "https://github.com/roocs/daops"),
            ],
            version="1.0",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True,
        )

    def _handler(self, request, response):
        # show me the environment used by the process in debug mode
        LOGGER.debug(f"Environment used in concat: {os.environ}")

        # from roocs_utils.exceptions import InvalidParameterValue, MissingParameterValue
        collections = parse_wps_input(
            request.inputs, "collections", as_sequence=True, must_exist=True
        )
        print(collections)
        inputs = {
            "collection": collections,
            "output_dir": self.workdir,
            "apply_fixes": parse_wps_input(request.inputs, "apply_fixes", default=True),
            "pre_checked": parse_wps_input(
                request.inputs, "pre_checked", default=False
            ),
        }

        # Let the director manage the processing or redirection to original files
        director = wrap_director(collections, inputs, run_concat)

        ml4 = build_metalink(
            "concat-result",
            "Concat result as NetCDF files.",
            self.workdir,
            director.output_uris,
        )

        populate_response(response, "concat", self.workdir, inputs, collections, ml4)
        return response
