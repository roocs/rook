import os

from jinja2 import Template
from pathlib import Path
from bs4 import BeautifulSoup
from pywps import get_ElementMakerForVersion
from pywps.app.basic import get_xpath_ns
from pywps.tests import WpsClient, WpsTestResponse

TESTS_HOME = os.path.abspath(os.path.dirname(__file__))
PYWPS_CFG = os.path.join(TESTS_HOME, "pywps.cfg")
ROOCS_CFG = os.path.join(TESTS_HOME, ".roocs.ini")

VERSION = "1.0.0"
WPS, OWS = get_ElementMakerForVersion(VERSION)
xpath_ns = get_xpath_ns(VERSION)

MINI_ESGF_CACHE_DIR = Path.home() / ".mini-esgf-data"
MINI_ESGF_MASTER_DIR = os.path.join(MINI_ESGF_CACHE_DIR, "master")


def write_roocs_cfg():
    cfg_templ = """
    [clisops:write]
    file_size_limit = 100KB

    [project:cmip5]
    base_dir = {{ base_dir }}/test_data/badc/cmip5/data/cmip5
    use_inventory = False

    [project:cmip6]
    base_dir = {{ base_dir }}/test_data/badc/cmip6/data/CMIP6
    use_inventory = False

    [project:cordex]
    base_dir = {{ base_dir }}/test_data/badc/cordex/data/cordex
    use_inventory = False

    [project:c3s-cmip5]
    base_dir = {{ base_dir }}/test_data/gws/nopw/j04/cp4cds1_vol1/data/c3s-cmip5

    [project:c3s-cmip6]
    base_dir = {{ base_dir }}/test_data/badc/cmip6/data/CMIP6

    [project:c3s-cmip6-decadal]
    base_dir = {{ base_dir }}/test_data/pool/data/CMIP6/data/CMIP6

    [project:c3s-cordex]
    base_dir = {{ base_dir }}/test_data/gws/nopw/j04/cp4cds1_vol1/data/c3s-cordex

    [project:c3s-cica-atlas]
    base_dir = {{ base_dir }}/test_data/pool/data/c3s-cica-atlas
    use_inventory = True
    use_catalog = True
    is_default_for_path = True
    file_name_template = {__derive__var_id}_{source}_{experiment_id}_{frequency}{__derive__time_range}{extra}.{__derive__extension}
    attr_defaults =
        frequency:no-freq
        experiment_id:no-expt
    facet_rule = variable project experiment time_frequency
    mappings =
        project:project_id
    data_node_root = https://data.mips.copernicus-climate.eu/thredds/fileServer/esg_c3s-cica-atlas/

    [dachar:store]
    store_type = elasticsearch

    [elasticsearch]
    endpoint = elasticsearch.ceda.ac.uk
    port = 443
    fix_store = c3s-roocs-fix
    fix_proposal_store = c3s-roocs-fix-prop
    """
    cfg = Template(cfg_templ).render(base_dir=MINI_ESGF_MASTER_DIR)
    with open(ROOCS_CFG, "w") as fp:
        fp.write(cfg)
    # point to roocs cfg in environment
    os.environ["ROOCS_CONFIG"] = ROOCS_CFG


def resource_file(filepath):
    return os.path.join(TESTS_HOME, "testdata", filepath)


class WpsTestClient(WpsClient):
    def get(self, *args, **kwargs):
        query = "?"
        for key, value in kwargs.items():
            query += "{}={}&".format(key, value)
        return super(WpsTestClient, self).get(query)


def client_for(service):
    return WpsTestClient(service, WpsTestResponse)


def get_output(doc):
    """Copied from pywps/tests/test_execute.py.
    TODO: make this helper method public in pywps."""
    output = {}
    for output_el in xpath_ns(
        doc, "/wps:ExecuteResponse" "/wps:ProcessOutputs/wps:Output"
    ):
        [identifier_el] = xpath_ns(output_el, "./ows:Identifier")

        lit_el = xpath_ns(output_el, "./wps:Data/wps:LiteralData")
        if lit_el != []:
            output[identifier_el.text] = lit_el[0].text

        ref_el = xpath_ns(output_el, "./wps:Reference")
        if ref_el != []:
            output[identifier_el.text] = ref_el[0].attrib["href"]

        data_el = xpath_ns(output_el, "./wps:Data/wps:ComplexData")
        if data_el != []:
            output[identifier_el.text] = data_el[0].text

    return output


def extract_paths_from_metalink(path):
    path = path.replace("file://", "")
    doc = BeautifulSoup(open(path, "r").read(), "xml")
    paths = [el.text.replace("file://", "") for el in doc.find_all("metaurl")]
    return paths
