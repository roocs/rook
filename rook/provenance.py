import os
from datetime import datetime

from prov.dot import prov_to_dot
from prov.model import ProvDocument


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
        self.doc.set_default_namespace(uri="http://purl.org/roocs/prov#")
        self.doc.add_namespace("prov", uri="http://www.w3.org/ns/prov#")
        self.doc.add_namespace(
            "provone", uri="http://purl.dataone.org/provone/2015/01/15/ontology#"
        )
        self.doc.add_namespace("dcterms", uri="http://purl.org/dc/terms/")
        # Define entities
        project_cds = self.doc.agent(
            ":copernicus_CDS",
            {
                "prov:type": "prov:Organization",
                "dcterms:title": "Copernicus Climate Data Store",
            },
        )
        self.sw_rook = self.doc.agent(
            ":rook",
            {
                "prov:type": "prov:SoftwareAgent",
                "dcterms:source": f"https://github.com/roocs/rook/releases/tag/v{rook_version}",
            },
        )
        self.doc.wasAttributedTo(self.sw_rook, project_cds)
        self.sw_daops = self.doc.agent(
            ":daops",
            {
                "prov:type": "prov:SoftwareAgent",
                "dcterms:source": f"https://github.com/roocs/daops/releases/tag/v{daops_version}",
            },
        )
        # workflow
        if workflow is True:
            self.workflow = self.doc.entity(
                ":workflow", {"prov:type": "provone:Workflow"}
            )
            orchestrate = self.doc.activity(
                ":orchestrate",
                other_attributes={
                    "prov:startedAtTime": datetime.now().isoformat(timespec='seconds'),
                    # "prov:endedAtTime": "2020-11-26T09:30:00",
                },
            )
            self.doc.wasAssociatedWith(
                orchestrate, agent=self.sw_rook, plan=self.workflow
            )

    def stop(self, workflow=False):
        if workflow is True:
            self.doc.activity(
                ":orchestrate",
                other_attributes={
                    "prov:endedAtTime": datetime.now().isoformat(timespec='seconds'),
                },
            )

    def add_operator(self, operator, parameters, collection, output):
        other_attributes = {}
        for param in ["time", "area", "level", "axes", "apply_fixes"]:
            if param in parameters:
                other_attributes[f":{param}"] = parameters[param]
        op = self.doc.activity(
            f":{operator}",
            other_attributes=other_attributes,
        )
        # input data
        ds_in = os.path.basename(collection[0])
        # ds_in_attrs = {
        #     'prov:type': 'provone:Data',
        #     'prov:value': f'{ds_in}',
        # }
        op_in = self.doc.entity(f":{ds_in}")
        # operator started by daops
        if self.workflow:
            self.doc.wasAssociatedWith(op, agent=self.sw_daops, plan=self.workflow)
        else:
            self.doc.start(op, starter=self.sw_daops, trigger=self.sw_rook)

        # Generated output file
        for out in output:
            ds_out = os.path.basename(out)
            # ds_out_attrs = {
            #     'prov:type': 'provone:Data',
            #     'prov:value': f'{ds_out}',
            # }
            op_out = self.doc.entity(f":{ds_out}")
            self.doc.wasDerivedFrom(op_out, op_in, activity=op)

    def write_json(self):
        outfile = os.path.join(self.output_dir, "provenance.json")
        self.doc.serialize(outfile, format="json")
        return outfile

    def write_png(self):
        outfile = os.path.join(self.output_dir, "provenance.png")
        figure = prov_to_dot(self.doc)
        figure.write_png(outfile)
        return outfile
