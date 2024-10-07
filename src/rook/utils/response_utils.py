from ..provenance import Provenance


def populate_response(response, label, workdir, inputs, collection, ml4):

    response.outputs["output"].data = ml4.xml

    # Collect provenance
    provenance = Provenance(workdir)
    provenance.start()
    urls = []

    for f in ml4.files:
        urls.extend(f.urls)

    provenance.add_operator(label, inputs, collection, urls)
    response.outputs["prov"].file = provenance.write_json()
    response.outputs["prov_plot"].file = provenance.write_png()
