import pytest

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
    assert doc["agent"]["id:C3S_CDS"]["prov:label"] == "Copernicus Climate Data Store"


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
    assert doc["agent"]["id:C3S_CDS"]["prov:label"] == "Copernicus Climate Data Store"
