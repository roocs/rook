import os

from prov.model import ProvDocument
from prov.dot import prov_to_dot


NS_URI_PREFIX = 'https://cds.climate.copernicus.eu/ns/'


class Provenance(object):
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.doc = None

    def build(self, operator, parameters, collection, output):
        from daops import __version__ as daops_version
        from rook import __version__ as rook_version
        self.doc = ProvDocument()
        # Declaring namespaces for various prefixes
        self.doc.add_namespace('prov', uri='http://www.w3.org/ns/prov#')  # prov standard
        self.doc.add_namespace('project', uri=NS_URI_PREFIX + 'project')  # copernicus, roocs
        # http://www.w3.org/ns/prov#SoftwareAgent
        self.doc.add_namespace('software', uri=NS_URI_PREFIX + 'software')  # rook, daops
        self.doc.add_namespace('workflow', uri=NS_URI_PREFIX + 'workflow')  # workflow description
        self.doc.add_namespace('operator', uri=NS_URI_PREFIX + 'operator')  # subset, aggregation etc
        self.doc.add_namespace('parameter', uri=NS_URI_PREFIX + 'parameter')  # operator parameter
        self.doc.add_namespace('collection', uri=NS_URI_PREFIX + 'collection')  # dataset collection
        self.doc.add_namespace('file', uri=NS_URI_PREFIX + 'file')  # netcdf, plots, metalink
        # Define entities
        project_cds = self.doc.agent('project:Copernicus Climate Data Store')
        sw_rook = self.doc.agent(f'software:rook=={rook_version}', {'prov:type': 'prov:SoftwareAgent'})
        # Relate rook to project
        self.doc.wasAttributedTo(sw_rook, project_cds)
        sw_daops = self.doc.agent(f'software:daops=={daops_version}', {'prov:type': 'prov:SoftwareAgent'})
        attributes = {
            'parameter:time': parameters.get('time'),
            'prov:startedAtTime': "2020-11-17T09:15:00",
            'prov:endedAtTime': "2020-11-17T09:30:00",
        }
        op = self.doc.activity(f'operator:{operator}', other_attributes=attributes)
        # Inout collection
        dataset = self.doc.entity(f'collection:{collection[0]}')
        # operator started by daops
        self.doc.start(op, starter=sw_daops, trigger=sw_rook)
        # Generated output file
        for mf in output.files:
            for url in mf.urls:
                out = self.doc.entity(f'file:{url}')
                self.doc.wasDerivedFrom(out, dataset, activity=op)

    def write_json(self):
        outfile = os.path.join(self.output_dir, 'provenance.json')
        self.doc.serialize(outfile, format='json')
        return outfile

    def write_png(self):
        outfile = os.path.join(self.output_dir, 'provenance.png')
        figure = prov_to_dot(self.doc)
        figure.write_png(outfile)
        return outfile
