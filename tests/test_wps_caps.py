from pywps import Service

from rook.processes import processes


def test_wps_caps(client_for):
    client = client_for(Service(processes=processes))
    resp = client.get(service="wps", request="getcapabilities", version="1.0.0")
    names = resp.xpath_text(
        "/wps:Capabilities" "/wps:ProcessOfferings" "/wps:Process" "/ows:Identifier"
    )
    assert sorted(names.split()) == [
        "average",
        "average_shape",
        "average_time",
        "concat",
        "dashboard",
        "orchestrate",
        "regrid",
        "subset",
        "usage",
        "weighted_average",
    ]
