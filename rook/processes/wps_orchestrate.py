from pywps import Process, ComplexInput, ComplexOutput
from pywps import FORMATS
from pywps.inout.outputs import MetaLink4, MetaFile

from rook import workflow


class Orchestrate(Process):
    def __init__(self):
        inputs = [
            ComplexInput('workflow', 'Workflow',
                         min_occurs=1,
                         max_occurs=1,
                         supported_formats=[FORMATS.JSON]),
        ]
        outputs = [
            ComplexOutput('output', 'Output',
                          as_reference=True,
                          supported_formats=[FORMATS.NETCDF]),
            ComplexOutput('output_meta4', 'METALINK v4 output',
                          abstract='Metalink v4 document with references to NetCDF files.',
                          as_reference=True,
                          supported_formats=[FORMATS.META4]),
        ]

        super(Orchestrate, self).__init__(
            self._handler,
            identifier='orchestrate',
            title='Orchestrate',
            abstract='Run a workflow',
            version='1.0',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):
        wf = workflow.WorkflowRunner(
            output_dir=self.workdir)
        output = wf.run(request.inputs['workflow'][0].file)
        # single netcdf file as output
        response.outputs['output'].file = output[0]
        # metalink document with collection of netcdf files
        ml4 = MetaLink4('workflow-result', 'Workflow result as NetCDF files.', workdir=self.workdir)
        for ncfile in output:
            mf = MetaFile('NetCDF file', 'NetCDF file', fmt=FORMATS.NETCDF)
            mf.file = ncfile
            ml4.append(mf)
        response.outputs['output_meta4'].data = ml4.xml
        return response
