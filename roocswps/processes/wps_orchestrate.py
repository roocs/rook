import json

from pywps import Process, ComplexInput, ComplexOutput
from pywps import FORMATS
from pywps import configuration

import daops

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
                          supported_formats=[FORMATS.TEXT]),
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
        config_args = {
            'data_root_dir': configuration.get_config_value("data", "cmip5_archive_root"),
            'output_dir': self.workdir,
            # 'chunk_rules': dconfig.chunk_rules,
            # 'filenamer': dconfig.filenamer,
        }

        wf = json.loads(request.inputs['workflow'][0].data)
        data_refs = wf['inputs']['data_ref']
        for step in wf['steps']:
            kwargs = {}
            if 'subset' in step:
                if 'time' in step['subset']:
                    kwargs['time'] = step['subset']['time'].split('/')
                kwargs.update(config_args)
                result = daops.subset(
                    data_refs,
                    **kwargs,
                    )
            # result.file_paths[0]
        response.outputs['output'].data = 'not working yet'
        return response
