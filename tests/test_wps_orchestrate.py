from pywps import Service
from pywps.tests import client_for, assert_response_success

from .common import get_output, resource_file, PYWPS_CFG
from rook.processes.wps_orchestrate import Orchestrate


def test_wps_orchestrate_simple():
    client = client_for(Service(processes=[Orchestrate()], cfgfiles=[PYWPS_CFG]))
    datainputs = "workflow=@xlink:href=file://{0};mode=simple".format(
        resource_file('subset_simple_wf.json'))
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=orchestrate&datainputs={}".format(
            datainputs))
    assert_response_success(resp)
    assert 'tas_mon_HadGEM2-ES_rcp85_r1i1p1_20850116-21201216.nc' in get_output(resp.xml)['output']


def test_wps_orchestrate_tree():
    client = client_for(Service(processes=[Orchestrate()], cfgfiles=[PYWPS_CFG]))
    datainputs = "workflow=@xlink:href=file://{0};mode=tree".format(
        resource_file('subset_wf_1.json'))
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=orchestrate&datainputs={}".format(
            datainputs))
    assert_response_success(resp)
    assert 'tas_mon_HadGEM2-ES_rcp85_r1i1p1_20850116-21201216.nc' in get_output(resp.xml)['output']
