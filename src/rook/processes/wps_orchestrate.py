import logging

from pywps import FORMATS, ComplexInput, ComplexOutput, Format, Process
from pywps.app.Common import Metadata
from pywps.app.exceptions import ProcessError

from rook import workflow

from ..utils.metalink_utils import build_metalink

LOGGER = logging.getLogger()


class Orchestrate(Process):
    def __init__(self):
        inputs = [
            ComplexInput(
                "workflow",
                "Workflow",
                min_occurs=1,
                max_occurs=1,
                supported_formats=[FORMATS.JSON],
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

        super().__init__(
            self._handler,
            identifier="orchestrate",
            title="Orchestrate",
            abstract="Run a workflow with combined operations. A workflow can be build using the rooki client.",
            metadata=[
                Metadata("Rooki", "https://github.com/roocs/rooki"),
            ],
            version="1.0",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True,
        )

    def _handler(self, request, response):
        try:
            wfdata = request.inputs["workflow"][0].data
            LOGGER.debug(f"type wfdata={type(wfdata)}, wfdata={wfdata}")
            # print(f"type wfdata={type(wfdata)}, wfdata={wfdata}")
            # workaround for CDATA issue in pywps
            # wfdata = wfdata.replace("<![CDATA[", "").replace("]]>", "")
            wf = workflow.WorkflowRunner(output_dir=self.workdir)
            file_uris = wf.run(wfdata)
        except Exception as e:
            raise ProcessError(f"{e}")

        # Metalink document with collection of netcdf files
        # ml4 = MetaLink4(
        #     "workflow-result", "Workflow result as NetCDF files.", workdir=self.workdir
        # )

        ml4 = build_metalink(
            "workflow-result",
            "Workflow result as NetCDF files.",
            self.workdir,
            file_uris,
        )

        # for ncfile in output:
        #     mf = MetaFile("NetCDF file", "NetCDF file", fmt=FORMATS.NETCDF)
        #     mf.file = ncfile
        #     ml4.append(mf)

        response.outputs["output"].data = ml4.xml
        response.outputs["prov"].file = wf.provenance.write_json()
        response.outputs["prov_plot"].file = wf.provenance.write_png()

        return response
