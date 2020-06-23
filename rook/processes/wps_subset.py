from pywps import Process, LiteralInput, ComplexOutput
from pywps import FORMATS
from pywps import configuration
from pywps.app.exceptions import ProcessError

from .utils import translate_args


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
                         default='0.,49.,10.,65',
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
        # TODO: handle lazy load of daops
        from daops.ops import subset
        from daops.utils import is_characterised
        data_refs = [dref.data for dref in request.inputs['data_ref']]
        if request.inputs['pre_checked'][0].data and not is_characterised(data_refs, require_all=True):
            raise ProcessError('Data has not been pre-checked')

        config_args = {
            'data_root_dir': configuration.get_config_value("data", "cmip5_archive_root"),
            'output_dir': self.workdir,
            # 'chunk_rules': dconfig.chunk_rules,
            # 'filenamer': dconfig.filenamer,
        }
        kwargs = translate_args(request)
        kwargs.update(config_args)

        result = subset(data_refs, **kwargs)
        response.outputs['output'].file = result.file_paths[0]
        return response
