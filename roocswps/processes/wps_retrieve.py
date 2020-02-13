from pywps import Process, LiteralInput, ComplexOutput
from pywps import FORMATS


class Retrieve(Process):
    def __init__(self):
        inputs = [
            LiteralInput('model', 'Model',
                         data_type='string',
                         default='giss_e2_h',),
            LiteralInput('variable', 'Variable',
                         data_type='string',
                         default='geopotential_height'),
            LiteralInput('experiment', 'Experiment',
                         data_type='string',
                         default='historical'),
            LiteralInput('ensemble_member', 'Ensemble Member',
                         data_type='string',
                         default='r6i1p2'),
            LiteralInput('format', 'Format',
                         data_type='string',
                         min_occurs=1,
                         max_occurs=1,
                         default='zip',
                         allowed_values=['zip', 'tgz']),
        ]
        outputs = [
            ComplexOutput('output', 'Output',
                          as_reference=True,
                          supported_formats=[FORMATS.TEXT]),
        ]

        super(Retrieve, self).__init__(
            self._handler,
            identifier='retrieve',
            title='Retrieve',
            version='1.0',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    @staticmethod
    def _handler(request, response):
        response.outputs['output'].data = 'not working yet'
        return response
