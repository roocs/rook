import pytest
from pywps import Service
from pywps.tests import assert_response_success, client_for

from rook.processes.wps_concat import Concat


@pytest.mark.xfail(reason="c3s-cmip6 decdal not in catalog")
def test_wps_concat_ec_earth(get_output, pywps_cfg):
    client = client_for(Service(processes=[Concat()], cfgfiles=[pywps_cfg]))
    datainputs = "collection=c3s-cmip6.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1960-r2i1p1f1.Amon.tas.gr.v20201215"  # noqa
    datainputs += ";collection=c3s-cmip6.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1960-r6i2p1f1.Amon.tas.gr.v20200508"  # noqa
    datainputs += ";dims=realization"
    request = "service=WPS&request=Execute&version=1.0.0&identifier=concat"
    resp = client.get(f"?{request}&datainputs={datainputs}")
    print(resp.data)
    assert_response_success(resp)
    assert "output" in get_output(resp.xml)
