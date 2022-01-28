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
from ..utils.subset_utils import run_subset

LOGGER = logging.getLogger()


class Subset(Process):
    def __init__(self):
        inputs = [
            LiteralInput(
                "collection",
                "Collection",
                abstract="A dataset identifier or list of comma separated identifiers"
                "Example: c3s-cmip5.output1.ICHEC.EC-EARTH.historical.day.atmos.day.r1i1p1.tas.latest",
                data_type="string",
                min_occurs=1,
                max_occurs=1,
            ),
            LiteralInput(
                "time",
                "Time Period",
                abstract="The time interval (start/end) to subset over separated by '/'"
                " or a list of time points separated by ','."
                " The format is according to the ISO-8601 standard."
                " Example: 1860-01-01/1900-12-30 or 1860-01-01, 1870-01-01, 1880-01-01",
                data_type="string",
                min_occurs=0,
                max_occurs=1,
            ),
            LiteralInput(
                "time_components",
                "Time Components",
                abstract="Optional time components to describe parts of the time period (e.g. year, month and day)."
                " Example: month:01,02,03 or year:1970,1980|month:01,02,03",
                data_type="string",
                min_occurs=0,
                max_occurs=1,
            ),
            LiteralInput(
                "area",
                "Area",
                abstract="The area to subset over as 4 comma separated values."
                "Example: 0.,49.,10.,65",
                data_type="string",
                min_occurs=0,
                max_occurs=1,
            ),
            LiteralInput(
                "level",
                "Level",
                abstract="The level range to subset over separated by a /"
                " or a list of level values separated by ','."
                "Example: 1000/2000 or 1000, 2000, 3000",
                data_type="string",
                min_occurs=0,
                max_occurs=1,
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
            LiteralInput(
                "original_files",
                "Original Files",
                data_type="boolean",
                abstract="Return original files only.",
                default="0",
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

        super(Subset, self).__init__(
            self._handler,
            identifier="subset",
            title="Subset",
            abstract="Run subsetting on climate model data. Calls daops operators.",
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
        collection = parse_wps_input(
            request.inputs, "collection", as_sequence=True, must_exist=True
        )

        inputs = {
            "collection": collection,
            "output_dir": self.workdir,
            "apply_fixes": parse_wps_input(
                request.inputs, "apply_fixes", default=True
            ),
            "pre_checked": parse_wps_input(
                request.inputs, "pre_checked", default=False
            ),
            "original_files": parse_wps_input(
                request.inputs, "original_files", default=False
            ),
            "time": parse_wps_input(request.inputs, "time", default=None),
            "time_components": parse_wps_input(request.inputs, "time_components", default=None),
            "level": parse_wps_input(request.inputs, "level", default=None),
            "area": parse_wps_input(request.inputs, "area", default=None),
        }

        # Let the director manage the processing or redirection to original files
        director = wrap_director(collection, inputs, run_subset)

        ml4 = build_metalink(
            "subset-result",
            "Subsetting result as NetCDF files.",
            self.workdir,
            director.output_uris,
        )

        populate_response(response, "subset", self.workdir, inputs, collection, ml4)
        return response
