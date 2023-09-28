import logging

from pywps import FORMATS, ComplexOutput, Format, LiteralInput, Process
from pywps.app.Common import Metadata
from pywps.app.exceptions import ProcessError
from pywps.inout.outputs import MetaFile, MetaLink4

from ..director import wrap_director
from ..utils.input_utils import parse_wps_input
from ..utils.metalink_utils import build_metalink
from ..utils.response_utils import populate_response
from ..utils.regrid_utils import run_regrid

LOGGER = logging.getLogger()


class Regrid(Process):
    def __init__(self):
        inputs = [
            LiteralInput(
                "collection",
                "Collection",
                abstract="A dataset identifier or list of comma separated identifiers. "
                "Example: c3s-cmip5.output1.ICHEC.EC-EARTH.historical.day.atmos.day.r1i1p1.tas.latest",
                data_type="string",
                min_occurs=1,
                max_occurs=1,
            ),
            LiteralInput(
                "method",
                "Regrid method",
                abstract="Please specify regridding method like consevative or bilinear. Default: nearest_s2d",
                data_type="string",
                min_occurs=1,
                max_occurs=1,
                allowed_values=["conservative", "patch", "nearest_s2d", "bilinear"],
                default="nearest_s2d",
            ),
            LiteralInput(
                "grid",
                "Regrid target grid",
                abstract="Please specify output grid resolution for regridding. Default: 1deg",
                data_type="string",
                min_occurs=1,
                max_occurs=1,
                allowed_values=["1deg", "2deg_lsm", "0pt25deg_era5_lsm"],
                default="1deg",
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

        super(Regrid, self).__init__(
            self._handler,
            identifier="regrid",
            title="Regrid",
            abstract="Run regridding operator on climate model data using daops (xarray).",
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
        # from roocs_utils.exceptions import InvalidParameterValue, MissingParameterValue
        collection = parse_wps_input(
            request.inputs, "collection", as_sequence=True, must_exist=True
        )

        inputs = {
            "collection": collection,
            "output_dir": self.workdir,
            "apply_fixes": False,
            "pre_checked": False,
            "method": parse_wps_input(request.inputs, "method", default="nearest_s2d"),
            "grid": parse_wps_input(request.inputs, "grid", default="1deg"),
        }
        # print(inputs)

        # Let the director manage the processing or redirection to original files
        director = wrap_director(collection, inputs, run_regrid)

        ml4 = build_metalink(
            "regrid-result",
            "regrid result as NetCDF files.",
            self.workdir,
            director.output_uris,
        )

        populate_response(response, "regrid", self.workdir, inputs, collection, ml4)
        return response
