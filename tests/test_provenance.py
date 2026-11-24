import prov.model
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


@pytest.mark.parametrize(
    ("parameter", "value", "expected"),
    [
        ("grid", (0.5,), "0.5"),
        ("grid", (1.0, 2.0), "1.0,2.0"),
        ("grid", (0.0, 360.0, 1.0, -90.0, 90.0, 1.0), "0.0,360.0,1.0,-90.0,90.0,1.0"),
        ("grid", [0.5], "0.5"),
        ("dims", ["time", "latitude"], "time,latitude"),
        ("grid", "auto", "auto"),
        ("adaptive_masking_threshold", 0.5, 0.5),
        ("apply_average", True, True),
    ],
)
def test_prov_operator_parameter_serialization(tmp_path, parameter, value, expected):
    provenance = Provenance(tmp_path)
    provenance.start()
    provenance.add_operator(
        "regrid", {parameter: value}, ["tas.nc"], ["tas_regridded.nc"]
    )

    doc = prov.model.ProvDocument.deserialize(provenance.write_json())
    [activity] = doc.get_records(prov.model.ProvActivity)
    attributes = dict(activity.attributes)
    assert attributes[doc.valid_qualified_name(f"roocs:{parameter}")] == expected
