from pywps import Service

from rook.processes import processes

from .common import client_for


def test_wps_caps():
    client = client_for(Service(processes=processes))
    resp = client.get(service="wps", request="getcapabilities", version="1.0.0")
    names = resp.xpath_text(
        "/wps:Capabilities" "/wps:ProcessOfferings" "/wps:Process" "/ows:Identifier"
    )
    assert sorted(names.split()) == [
        "average_time",
        "dashboard",
        "orchestrate",
        "subset",
        "usage",
    ]
