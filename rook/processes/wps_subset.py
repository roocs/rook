from pywps import Process, LiteralInput, ComplexOutput
from pywps import FORMATS
from pywps import configuration
from pywps.app.exceptions import ProcessError

from roocs_utils.parameter import parameterise


class Subset(Process):
    def __init__(self):
        inputs = [
            LiteralInput('collection', 'Collection',
                         data_type='string',
                         default='cmip5.output1.MOHC.HadGEM2-ES.rcp85.mon.atmos.Amon.r1i1p1.latest.tas',
                         min_occurs=1,
                         max_occurs=10,),
            LiteralInput('time', 'Time Period',
                         data_type='string',
                         default="2085-01-01/2120-12-30",
                         min_occurs=1,
                         max_occurs=1,),
            LiteralInput('area', 'Area',
                         data_type='string',
                         default='0.,49.,10.,65',
                         min_occurs=0,
                         max_occurs=1,),
            LiteralInput('level', 'Level',
                         data_type='string',
                         default='0/1000',
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
        from daops.ops.subset import subset
        from daops.utils import is_characterised
        collection = [col.data for col in request.inputs['collection']]
        if request.inputs['pre_checked'][0].data and not is_characterised(collection, require_all=True):
            raise ProcessError('Data has not been pre-checked')

        config_args = {
            'output_dir': self.workdir,
            # 'chunk_rules': dconfig.chunk_rules,
            # 'filenamer': dconfig.filenamer,
        }

        kwargs = parameterise.parameterise(collection=collection,
                                           time=request.inputs['time'][0].data,
                                           level=request.inputs['level'][0].data,
                                           area=request.inputs['area'][0].data)
        kwargs.update(config_args)
        result = subset(**kwargs)
        response.outputs['output'].file = result.file_paths[0]
        return response
