from pywps import Process, ComplexInput, ComplexOutput
from pywps import FORMATS, Format
from pywps.app.exceptions import ProcessError
from pywps.app.Common import Metadata
from pywps.inout.outputs import MetaLink4, MetaFile

from rook import workflow
from ..provenance import Provenance


class Orchestrate(Process):
    def __init__(self):
        inputs = [
            ComplexInput('workflow', 'Workflow',
                         min_occurs=1,
                         max_occurs=1,
                         supported_formats=[FORMATS.JSON]),
        ]
        outputs = [
            ComplexOutput('output', 'METALINK v4 output',
                          abstract='Metalink v4 document with references to NetCDF files.',
                          as_reference=True,
                          supported_formats=[FORMATS.META4]),
            ComplexOutput('prov', 'Provenance',
                          abstract='Provenance document using W3C standard.',
                          as_reference=True,
                          supported_formats=[FORMATS.JSON]),
            ComplexOutput('prov_plot', 'Provenance Diagram',
                          abstract='Provenance document as diagram.',
                          as_reference=True,
                          supported_formats=[Format('image/png', extension='.png', encoding='base64')]),
        ]

        super(Orchestrate, self).__init__(
            self._handler,
            identifier='orchestrate',
            title='Orchestrate',
            abstract='Run a workflow with combined operations. A workflow can be build using the rooki client.',
            metadata=[
                Metadata('Rooki', 'https://github.com/roocs/rooki'),
            ],
            version='1.0',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):
        try:
            wf = workflow.WorkflowRunner(
                output_dir=self.workdir)
            output = wf.run(request.inputs['workflow'][0].file)
        except Exception as e:
            raise ProcessError(f"{e}")
        # metalink document with collection of netcdf files
        ml4 = MetaLink4('workflow-result', 'Workflow result as NetCDF files.', workdir=self.workdir)
        for ncfile in output:
            mf = MetaFile('NetCDF file', 'NetCDF file', fmt=FORMATS.NETCDF)
            mf.file = ncfile
            ml4.append(mf)
        response.outputs['output'].data = ml4.xml
        # collect provenance
        provenance = Provenance(self.workdir)
        provenance.start()
        provenance.add_workflow()
        response.outputs['prov'].file = provenance.write_json()
        response.outputs['prov_plot'].file = provenance.write_png()
        return response
