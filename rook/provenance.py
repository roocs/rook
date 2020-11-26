import os

from prov.model import ProvDocument
from prov.dot import prov_to_dot


class Provenance(object):
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.doc = None
        self.workflow = None

    def start(self, workflow=False):
        from daops import __version__ as daops_version
        from rook import __version__ as rook_version
        self.doc = ProvDocument()
        # Declaring namespaces for various prefixes
        self.doc.add_namespace('prov', uri='http://www.w3.org/ns/prov#')  # prov standard
        self.doc.add_namespace("dcterms", "http://purl.org/dc/terms/")  # dublin core
        self.doc.add_namespace('copernicus', uri='https://copernicus.eu/ns/copernicus')  # copernicus cds
        self.doc.add_namespace('roocs', uri='https://roocs.org/ns/roocs')  # copernicus cds
        # Define entities
        project_cds = self.doc.agent('copernicus:CDS', {
            'prov:type': 'prov:Organization',
            'dcterms:title': 'Copernicus Climate Data Store',
        })
        self.sw_rook = self.doc.agent('roocs:rook', {
            'prov:type': 'prov:SoftwareAgent',
            'dcterms:source': f'https://github.com/roocs/rook/releases/tag/v{rook_version}',
        })
        # Relate rook to project
        self.doc.wasAttributedTo(self.sw_rook, project_cds)
        self.sw_daops = self.doc.agent('roocs:daops', {
            'prov:type': 'prov:SoftwareAgent',
            'dcterms:source': f'https://github.com/roocs/daops/releases/tag/v{daops_version}',
        })
        # workflow
        if workflow is True:
            self.workflow = self.doc.entity(
                "roocs:workflow", {"prov:type": "prov:Plan",
                                   "prov:startedAtTime": "2020-11-26T09:15:00",
                                   "prov:endedAtTime": "2020-11-26T09:30:00",
                                   })

    def add_operator(self, operator, parameters, collection, output):
        op = self.doc.activity(f'roocs:{operator}', other_attributes={
            'roocs:time': parameters.get('time'),
            'prov:type': 'roocs:operator',
        })
        # input collection
        dataset = self.doc.entity(f'roocs:{collection[0]}', {
            'prov:type': 'roocs:collection',
            'prov:label': f'{collection[0]}',
        })
        # operator started by daops
        self.doc.start(op, starter=self.sw_daops, trigger=self.sw_rook)
        if self.workflow:
            self.doc.wasAssociatedWith(
                op,
                agent=self.sw_daops,
                plan=self.workflow)
        # Generated output file
        for url in output:
            out = self.doc.entity(f'roocs:{os.path.basename(url)}', {
                'dcterms:source': f'{os.path.basename(url)}',
                'dcterms:format': 'NetCDF',
            })
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
