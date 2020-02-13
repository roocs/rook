from pywps import Process, LiteralInput, ComplexOutput
from pywps import FORMATS


class Subset(Process):
    def __init__(self):
        inputs = [
            LiteralInput('period', 'Time Period',
                         abstract='Please enter the time period: 195001-190012',
                         data_type='string'),
            LiteralInput('area', 'Bounding Box',
                         abstract='Please enter the bbox: -10, -10, 10, 10',
                         data_type='string'),
        ]
        outputs = [
            ComplexOutput('output', 'Output',
                          as_reference=True,
                          supported_formats=[FORMATS.TEXT]),
        ]

        super(Subset, self).__init__(
            self._handler,
            identifier='subset',
            title='Subset',
            abstract='Run subsetting on climate data.',
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
