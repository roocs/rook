from pywps import Process, LiteralInput, ComplexOutput
from pywps import FORMATS
from pywps.app.exceptions import ProcessError
from pywps.inout.outputs import MetaLink4, MetaFile


from roocs_utils.parameter import parameterise


class Subset(Process):
    def __init__(self):
        inputs = [
            LiteralInput('collection', 'Collection',
                         abstract='c3s-cmip5.output1.ICHEC.EC-EARTH.historical.day.atmos.day.r1i1p1.tas.latest',
                         data_type='string',
                         min_occurs=1,
                         max_occurs=1,),
            LiteralInput('time', 'Time Period',
                         abstract='Example: 1860-01-01/1900-12-30',
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
            ComplexOutput('output', 'METALINK v4 output',
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
        # from roocs_utils.exceptions import InvalidParameterValue, MissingParameterValue
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
        try:
            kwargs = parameterise.parameterise(**subset_args)
            kwargs.update(config_args)
            result = subset(**kwargs)
        except Exception as e:
            raise ProcessError(f"{e}")
        # metalink document with collection of netcdf files
        ml4 = MetaLink4('subset-result', 'Subsetting result as NetCDF files.', workdir=self.workdir)
        for ncfile in result.file_paths:
            mf = MetaFile('NetCDF file', 'NetCDF file', fmt=FORMATS.NETCDF)
            mf.file = ncfile
            ml4.append(mf)
        response.outputs['output'].data = ml4.xml
        return response
