from pywps import Process, LiteralInput, ComplexOutput
from pywps import FORMATS
from pywps.app.exceptions import ProcessError

import daops
import daops.config as dconfig

class Subset(Process):
    def __init__(self):
        inputs = [
            LiteralInput('data_ref', 'Data references',
                         data_type='string',
                         default='cmip5.output1.MOHC.HadGEM2-ES.rcp85.mon.atmos.Amon.r1i1p1.latest.tas',
                         min_occurs=1,
                         max_occurs=10,),
            LiteralInput('time', 'Time Period',
                         data_type='string',
                         default="2085-01-01/2120-12-30",
                         min_occurs=1,
                         max_occurs=1,),
            LiteralInput('space', 'Bounding Box',
                         data_type='string',
                         default='-5.,49.,10.,65',
                         min_occurs=0,
                         max_occurs=1,),
            LiteralInput('level', 'Level',
                         data_type='integer',
                         default='1000',
                         min_occurs=0,
                         max_occurs=10,),
            LiteralInput('pre_checked', 'Pre-Checked', data_type='boolean',
                         abstract='Use checked data only.',
                         default='0',
                         min_occurs=1,
                         max_occurs=1),
        ]
        outputs = [
            ComplexOutput('output', 'Output',
                          as_reference=True,
                          supported_formats=[FORMATS.NETCDF]),
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

    def _handler(self, request, response):
        data_refs = [dref.data for dref in request.inputs['data_ref']]
        if request.inputs['pre_checked'][0].data and not daops.is_characterised(data_refs, require_all=True):
            raise ProcessError('Data has not been pre-checked')

        if 'time' in request.inputs:
            value = request.inputs['time'][0].data
            time = value.split('/')
        else:
            time = None

        if 'space' in request.inputs:
            value = request.inputs['space'][0].data
            space = [float(_) for _ in value.split(',')]
        else:
            space = None

        if 'level' in request.inputs:
            level = request.inputs['level'][0].data
        else:
            level = None

        result = daops.subset(
            data_refs,
            time=time,
            # space=space,
            # level=level,
            output_dir=self.workdir,
            # chunk_rules=None,
            # filenamer=None,
            )
        response.outputs['output'].file = result.file_paths[0]
        return response
