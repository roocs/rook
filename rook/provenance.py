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
        self.doc.set_default_namespace(uri='http://purl.org/roocs/prov#')
        self.doc.add_namespace('prov', uri='http://www.w3.org/ns/prov#')
        self.doc.add_namespace('provone', uri='http://purl.dataone.org/provone/2015/01/15/ontology#')
        self.doc.add_namespace('dcterms', uri='http://purl.org/dc/terms/')
        # Define entities
        project_cds = self.doc.agent(':copernicus_CDS', {
            'prov:type': 'prov:Organization',
            'dcterms:title': 'Copernicus Climate Data Store',
        })
        self.sw_rook = self.doc.agent(':rook', {
            'prov:type': 'prov:SoftwareAgent',
            'dcterms:source': f'https://github.com/roocs/rook/releases/tag/v{rook_version}',
        })
        self.doc.wasAttributedTo(self.sw_rook, project_cds)
        self.sw_daops = self.doc.agent(':daops', {
            'prov:type': 'prov:SoftwareAgent',
            'dcterms:source': f'https://github.com/roocs/daops/releases/tag/v{daops_version}',
        })
        # workflow
        if workflow is True:
            self.workflow = self.doc.entity(
                ":workflow", {"prov:type": "provone:Workflow"})
            orchestrate = self.doc.activity(":orchestrate", other_attributes={
                "prov:startedAtTime": "2020-11-26T09:15:00",
                "prov:endedAtTime": "2020-11-26T09:30:00",
            })
            self.doc.wasAssociatedWith(orchestrate, agent=self.sw_rook, plan=self.workflow)

    def add_operator(self, operator, parameters, collection, output):
        op = self.doc.activity(f':{operator}', other_attributes={
            ':time': parameters.get('time'),
        })
        # input data
        op_in = self.doc.entity(f':{operator}_in', {
            'prov:type': 'provone:Data',
            'prov:value': f'{collection[0]}',
        })
        # operator started by daops
        if self.workflow:
            self.doc.wasAssociatedWith(
                op,
                agent=self.sw_daops,
                plan=self.workflow)
        else:
            self.doc.start(op, starter=self.sw_daops, trigger=self.sw_rook)
        # Generated output file
        op_out = self.doc.entity(f':{operator}_out', {
            'prov:type': 'provone:Data',
            'prov:value': f'{os.path.basename(output[0])}',
        })
        self.doc.wasDerivedFrom(op_out, op_in, activity=op)

    def write_json(self):
        outfile = os.path.join(self.output_dir, 'provenance.json')
        self.doc.serialize(outfile, format='json')
        return outfile

    def write_png(self):
        outfile = os.path.join(self.output_dir, 'provenance.png')
        figure = prov_to_dot(self.doc)
        figure.write_png(outfile)
        return outfile
