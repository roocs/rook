from pywps import Process, LiteralInput, ComplexOutput
from pywps import FORMATS, Format
from pywps.app.exceptions import ProcessError
from pywps.app.Common import Metadata
from pywps.inout.outputs import MetaLink4, MetaFile

from ..provenance import Provenance


class Average(Process):
    def __init__(self):
        inputs = [
            LiteralInput('collection', 'Collection',
                         data_type='string',
                         default='c3s-cmip5.output1.ICHEC.EC-EARTH.historical.day.atmos.day.r1i1p1.tas.latest',
                         min_occurs=1,
                         max_occurs=1,),
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
            LiteralInput('apply_fixes', 'Apply Fixes', data_type='boolean',
                         abstract='Apply fixes to datasets.',
                         default='1',
                         min_occurs=1,
                         max_occurs=1),
        ]
        outputs = [
            ComplexOutput('output', 'METALINK v4 output',
                          abstract='Metalink v4 document with references to NetCDF files.',
                          as_reference=True,
                          supported_formats=[FORMATS.META4]),
            ComplexOutput('prov', 'Provenance',
                          abstract='Provenance document using W3C standard.',
                          as_reference=True,
                          supported_formats=[FORMATS.JSON]),
            ComplexOutput('prov_plot', 'Provenance Diagram',
                          abstract='Provenance document as diagram.',
                          as_reference=True,
                          supported_formats=[Format('image/png', extension='.png', encoding='base64')]),
        ]

        super(Average, self).__init__(
            self._handler,
            identifier='average',
            title='Average',
            abstract='Run averaging on climate model data. Calls daops operators.',
            metadata=[
                Metadata('DAOPS', 'https://github.com/roocs/daops'),
            ],
            version='1.0',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):
        # TODO: handle lazy load of daops
        from daops.utils import is_characterised
        collection = [dset.data for dset in request.inputs['collection']]
        if request.inputs['pre_checked'][0].data and not is_characterised(collection, require_all=True):
            raise ProcessError('Data has not been pre-checked')
        average_args = {
            'collection': collection,
        }
        if 'axes' in request.inputs:
            average_args['axes'] = request.inputs['axes'][0].data
        # metalink document with collection of netcdf files
        ml4 = MetaLink4('average-result', 'Averaging result as NetCDF files.', workdir=self.workdir)
        mf = MetaFile('Text file', 'Dummy text file', fmt=FORMATS.TEXT)
        mf.data = 'not working yet'
        ml4.append(mf)
        response.outputs['output'].data = ml4.xml
        # collect provenance
        provenance = Provenance(self.workdir)
        provenance.start()
        urls = []
        for f in ml4.files:
            urls.extend(f.urls)
        provenance.add_operator('average', average_args, collection, urls)
        response.outputs['prov'].file = provenance.write_json()
        response.outputs['prov_plot'].file = provenance.write_png()
        return response
