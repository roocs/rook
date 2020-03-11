from pywps import Process, ComplexInput, ComplexOutput, LiteralInput
from pywps import FORMATS
from pywps import configuration

from roocswps import workflow


class Orchestrate(Process):
    def __init__(self):
        inputs = [
            ComplexInput('workflow', 'Workflow',
                         min_occurs=1,
                         max_occurs=1,
                         supported_formats=[FORMATS.JSON]),
            LiteralInput('mode', 'Mode',
                         data_type='string',
                         min_occurs=1,
                         max_occurs=1,
                         default='tree',
                         allowed_values=['tree', 'simple']),
        ]
        outputs = [
            ComplexOutput('output', 'Output',
                          as_reference=True,
                          supported_formats=[FORMATS.NETCDF]),
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
        if request.inputs['mode'][0].data == 'simple':
            wf = workflow.SimpleWorkflow(
                data_root_dir=configuration.get_config_value("data", "cmip5_archive_root"),
                output_dir=self.workdir)
        else:
            wf = workflow.TreeWorkflow(
                data_root_dir=configuration.get_config_value("data", "cmip5_archive_root"),
                output_dir=self.workdir)
        output = wf.run(request.inputs['workflow'][0].file)
        response.outputs['output'].file = output[0]
        return response
