import os

from pywps import Process, LiteralInput, ComplexOutput
from pywps import FORMATS, Format
from pywps.app.exceptions import ProcessError
from pywps.app.Common import Metadata
from pywps.inout.outputs import MetaLink4, MetaFile

from ..director import Director
from ..provenance import Provenance


import logging

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
                abstract="The time period to subset over separated by /"
                "Example: 1860-01-01/1900-12-30",
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
                "Example: 0/1000",
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
                default="0",
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
        # TODO: handle lazy load of daops
        from daops.ops.subset import subset
        from daops.utils.normalise import ResultSet

        # show me the environment used by the process in debug mode
        LOGGER.debug(f"Environment used in subset: {os.environ}")

        # from roocs_utils.exceptions import InvalidParameterValue, MissingParameterValue
        collection = [dset.data for dset in request.inputs["collection"]]

        config_args = {
            "output_dir": self.workdir,
            "apply_fixes": request.inputs["apply_fixes"][0].data,
            "pre_checked": request.inputs["pre_checked"][0].data,
            "original_files": request.inputs["original_files"][0].data
            # 'chunk_rules': dconfig.chunk_rules,
            # 'filenamer': dconfig.filenamer,
        }

        subset_args = {
            "collection": collection,
        }
        if "time" in request.inputs:
            subset_args["time"] = request.inputs["time"][0].data
        if "level" in request.inputs:
            subset_args["level"] = request.inputs["level"][0].data
        if "area" in request.inputs:
            subset_args["area"] = request.inputs["area"][0].data

        subset_args.update(config_args)

        # Ask director whether request should be rejected, use original files or apply WPS process
        try:
            director = Director(collection, subset_args)
        except Exception as e:
            raise ProcessError(f"{e}")

        # If original files should be returned...
        if director.use_original_files:
            result = ResultSet()

            for ds_id, file_urls in director.original_file_urls.items():
                result.add(ds_id, file_urls)

        # else: generate the new subset of files
        else:
            del subset_args["pre_checked"]
            del subset_args["original_files"]
            try:
                result = subset(**subset_args)
            except Exception as e:
                raise ProcessError(f"{e}")

        # metalink document with collection of netcdf files/ urls
        ml4 = MetaLink4(
            "subset-result", "Subsetting result as NetCDF files.", workdir=self.workdir
        )

        # need to handle file URLS
        for result in result.file_uris:
            mf = MetaFile("NetCDF file", "NetCDF file", fmt=FORMATS.NETCDF)

            if director.use_original_files:
                mf.url = result
            else:
                mf.file = result
            ml4.append(mf)

        response.outputs["output"].data = ml4.xml

        # collect provenance
        provenance = Provenance(self.workdir)
        provenance.start()
        urls = []

        for f in ml4.files:
            urls.extend(f.urls)

        provenance.add_operator("subset", subset_args, collection, urls)
        response.outputs["prov"].file = provenance.write_json()
        response.outputs["prov_plot"].file = provenance.write_png()

        return response
