from pywps import Process, LiteralInput, ComplexOutput
from pywps import FORMATS
from pywps.app.exceptions import ProcessError
from pywps.inout.outputs import MetaLink4, MetaFile

from roocs_utils.parameter import parameterise


class Subset(Process):
    def __init__(self):
        inputs = [
            LiteralInput('collection', 'Collection',
                         abstract='cmip5.output1.MOHC.HadGEM2-ES.rcp85.mon.atmos.Amon.r1i1p1.latest.tas',
                         data_type='string',
                         min_occurs=1,
                         max_occurs=1,),
            LiteralInput('time', 'Time Period',
                         abstract='Example: 2085-01-01/2120-12-30',
                         data_type='string',
                         min_occurs=0,
                         max_occurs=1,),
            LiteralInput('area', 'Area',
                         abstract="Example: 0.,49.,10.,65",
                         data_type='string',
                         min_occurs=0,
                         max_occurs=1,),
            LiteralInput('level', 'Level',
                         abstract="Example: 0/1000",
                         data_type='string',
                         min_occurs=0,
                         max_occurs=1,),
            LiteralInput('pre_checked', 'Pre-Checked', data_type='boolean',
                         abstract='Use checked data only.',
                         default='0',
                         min_occurs=1,
                         max_occurs=1),
        ]
        outputs = [
            ComplexOutput('output', 'Output',
                          abstract='A single NetCDF file.',
                          as_reference=True,
                          supported_formats=[FORMATS.NETCDF]),
            ComplexOutput('output_meta4', 'METALINK v4 output',
                          abstract='Metalink v4 document with references to NetCDF files.',
                          as_reference=True,
                          supported_formats=[FORMATS.META4]),
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
        collection = [dset.data for dset in request.inputs['collection']]
        if request.inputs['pre_checked'][0].data and not is_characterised(collection, require_all=True):
            raise ProcessError('Data has not been pre-checked')

        config_args = {
            'output_dir': self.workdir,
            # 'chunk_rules': dconfig.chunk_rules,
            # 'filenamer': dconfig.filenamer,
        }

        subset_args = {
            'collection': collection,
        }
        if 'time' in request.inputs:
            subset_args['time'] = request.inputs['time'][0].data
        if 'level' in request.inputs:
            subset_args['level'] = request.inputs['level'][0].data
        if 'area' in request.inputs:
            subset_args['area'] = request.inputs['area'][0].data
        kwargs = parameterise.parameterise(**subset_args)
        kwargs.update(config_args)
        result = subset(**kwargs)
        response.outputs['output'].file = result.file_paths[0]
        # metalink document with collection of netcdf files
        ml4 = MetaLink4('subset-result', 'Subsetting result as NetCDF files.', workdir=self.workdir)
        for ncfile in result.file_paths:
            mf = MetaFile('NetCDF file', 'NetCDF file', fmt=FORMATS.NETCDF)
            mf.file = ncfile
            ml4.append(mf)
        response.outputs['output_meta4'].data = ml4.xml
        return response
