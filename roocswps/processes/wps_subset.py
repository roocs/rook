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
                         default="cmip6.ukesm1.r1.gn.tasmax.v20200101",
                         min_occurs=1,
                         max_occurs=10,),
            LiteralInput('time', 'Time Period',
                         data_type='string',
                         default="1999-01-01T00:00:00/2100-12-30T00:00:00",
                         min_occurs=1,
                         max_occurs=1,),
            LiteralInput('space', 'Bounding Box',
                         data_type='string',
                         default='-5.,49.,10.,65',
                         min_occurs=1,
                         max_occurs=1,),
            LiteralInput('level', 'Level',
                         data_type='integer',
                         default='1000',
                         min_occurs=1,
                         max_occurs=10,),
            LiteralInput('pre_checked', 'Pre-Checked', data_type='boolean',
                         abstract='Use checked data only.',
                         default='0'),
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
        if pre_checked and not daops.is_characterised(data_refs, require_all=True):
            raise ProcessError('Data has not been pre-checked')

        config_args = {'output_dir': self.workdir,
                       'chunk_rules': dconfig.chunk_rules,
                       'filenamer': dconfig.filenamer}

        kwargs = {}
        kwargs['time'] = request.inputs['time'][0].data
        kwargs['space'] = request.inputs['space'][0].data
        kwargs['level'] = request.inputs['level'][0].data
        kwargs.update(config_args)

        response.outputs['output'].file = daops.subset(data_refs, **kwargs)
        return response
