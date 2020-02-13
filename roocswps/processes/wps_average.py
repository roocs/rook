from pywps import Process, LiteralInput, ComplexOutput
from pywps import FORMATS


class Average(Process):
    def __init__(self):
        inputs = [
            LiteralInput('axes', 'Axes',
                         abstract='Please choose an axes for averaging.',
                         data_type='string',
                         min_occurs=1,
                         max_occurs=1,
                         default='time',
                         allowed_values=['time', 'latitude', 'longitude']),
        ]
        outputs = [
            ComplexOutput('output', 'Output',
                          as_reference=True,
                          supported_formats=[FORMATS.TEXT]),
        ]

        super(Average, self).__init__(
            self._handler,
            identifier='average',
            title='Average',
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
