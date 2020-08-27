from pywps import Process, LiteralInput, ComplexOutput
from pywps import FORMATS
from pywps.app.exceptions import ProcessError
from pywps.inout.outputs import MetaLink4, MetaFile


class Average(Process):
    def __init__(self):
        inputs = [
            LiteralInput('data_ref', 'Data references',
                         data_type='string',
                         default='cmip5.output1.MOHC.HadGEM2-ES.rcp85.mon.atmos.Amon.r1i1p1.latest.tas',
                         min_occurs=1,
                         max_occurs=10,),
            LiteralInput('axes', 'Axes',
                         abstract='Please choose an axes for averaging.',
                         data_type='string',
                         min_occurs=1,
                         max_occurs=1,
                         default='time',
                         allowed_values=['time', 'latitude', 'longitude']),
            LiteralInput('pre_checked', 'Pre-Checked', data_type='boolean',
                         abstract='Use checked data only.',
                         default='0',
                         min_occurs=1,
                         max_occurs=1),
        ]
        outputs = [
            ComplexOutput('output', 'Output',
                          as_reference=True,
                          supported_formats=[FORMATS.TEXT]),
            ComplexOutput('output_meta4', 'METALINK v4 output',
                          abstract='Metalink v4 document with references to NetCDF files.',
                          as_reference=True,
                          supported_formats=[FORMATS.META4]),
        ]

        super(Average, self).__init__(
            self._handler,
            identifier='average',
            title='Average',
            abstract='Run averaging on climate data.',
            version='1.0',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    @staticmethod
    def _handler(request, response):
        # TODO: handle lazy load of daops
        from daops.utils import is_characterised
        data_refs = [dref.data for dref in request.inputs['data_ref']]
        if request.inputs['pre_checked'][0].data and not is_characterised(data_refs, require_all=True):
            raise ProcessError('Data has not been pre-checked')
        # single netcdf file as output
        response.outputs['output'].data = 'not working yet'
        # metalink document with collection of netcdf files
        ml4 = MetaLink4('average-result', 'Averaging result as NetCDF files.', workdir=self.workdir)
        mf = MetaFile('Text file', 'Dummy text file', fmt=FORMATS.TEXT)
        mf.data = 'not working yet'
        ml4.append(mf)
        response.outputs['output_meta4'].data = ml4.xml
        return response
