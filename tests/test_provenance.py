from rook.provenance import Provenance


def test_prov_simple(tmpdir):
    prov = Provenance(tmpdir)
    prov.start()
    prov.add_operator(
        "subset", {"time": "2010/2020"}, ["tas_yearly.nc"], ["tas_2010_2020.nc"]
    )
    prov.add_operator(
        "subset", {"time": "2010/2012"}, ["tas_2010_2020.nc"], ["tas_2010_2012.nc"]
    )
    doc = prov.json()
    assert (
        doc["agent"]["roocs:C3S_CDS"]["prov:label"] == "Copernicus Climate Data Store"
    )
    assert doc["agent"]["roocs:Provider"]["prov:label"] == "Provider"


def test_prov_workflow(tmpdir):
    prov = Provenance(tmpdir)
    prov.start(workflow=True)
    prov.add_operator(
        "subset", {"time": "2010/2020"}, ["tas_yearly.nc"], ["tas_2010_2020.nc"]
    )
    prov.add_operator(
        "subset", {"time": "2010/2012"}, ["tas_2010_2020.nc"], ["tas_2010_2012.nc"]
    )
    prov.stop()
    doc = prov.json()
    assert (
        doc["agent"]["roocs:C3S_CDS"]["prov:label"] == "Copernicus Climate Data Store"
    )
    assert doc["agent"]["roocs:Provider"]["prov:label"] == "Provider"


def test_prov_operator_records_representative_input_and_output(tmpdir):
    prov = Provenance(tmpdir)
    prov.start(workflow=True)
    prov.add_operator(
        "average",
        {"dims": "time"},
        ["tas_2000_2004.nc", "tas_2005_2009.nc"],
        ["tas_2000_2004_avg.nc", "tas_2005_2009_avg.nc"],
    )

    provn = prov.get_provn()
    assert "wasDerivedFrom(roocs:tas_2000_2004_avg.nc, roocs:tas_2000_2004.nc" in provn
    assert "tas_2005_2009.nc" not in provn
    assert "tas_2005_2009_avg.nc" not in provn
