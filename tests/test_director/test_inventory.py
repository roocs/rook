from rook.director.inventory import Inventory


inv = None
ds_id = "CMIP6.ScenarioMIP.NCC.NorESM2-LM.ssp245.r1i1p1f1.Amon.hfss.gn.v20191108"


def setup_module():
    global inv
    inv = Inventory("c3s-cmip6")


def test_inventory_type():
    assert isinstance(inv, Inventory)


def test_inventory_c3s_cmip6():
    assert isinstance(inv, Inventory)

    project = "c3s-cmip6"
    assert inv.project == project
    assert inv.base_dir == "/badc/cmip6/data"
    assert len(inv) > 1400


def test_inventory_contains():
    assert inv.contains([ds_id])
    assert not inv.contains(["nonsense"])


def test_inventory_get_matches():
    assert inv.get_matches(["nonsense"]) is False

    expected = {
        "ds_id": ds_id,
        "path": "CMIP6/ScenarioMIP/NCC/NorESM2-LM/ssp245/r1i1p1f1/Amon/hfss/gn/v20191108",
        "size": 61055040,
        "files": """hfss_Amon_NorESM2-LM_ssp245_r1i1p1f1_gn_201501-202012.nc
hfss_Amon_NorESM2-LM_ssp245_r1i1p1f1_gn_202101-203012.nc
hfss_Amon_NorESM2-LM_ssp245_r1i1p1f1_gn_203101-204012.nc
hfss_Amon_NorESM2-LM_ssp245_r1i1p1f1_gn_204101-205012.nc
hfss_Amon_NorESM2-LM_ssp245_r1i1p1f1_gn_205101-206012.nc
hfss_Amon_NorESM2-LM_ssp245_r1i1p1f1_gn_206101-207012.nc
hfss_Amon_NorESM2-LM_ssp245_r1i1p1f1_gn_207101-208012.nc
hfss_Amon_NorESM2-LM_ssp245_r1i1p1f1_gn_208101-209012.nc
hfss_Amon_NorESM2-LM_ssp245_r1i1p1f1_gn_209101-210012.nc""".strip().split(),
    }

    record = inv.get_matches([ds_id])[ds_id]

    for key, value in expected.items():
        assert value == record[key]


def test_inventory_get_file_paths():
    first_file = inv.get_file_paths([ds_id])[ds_id][0]

    expected_file = (
        "/badc/cmip6/data/CMIP6/ScenarioMIP/NCC/NorESM2-LM/ssp245/r1i1p1f1/Amon/"
        "hfss/gn/v20191108/hfss_Amon_NorESM2-LM_ssp245_r1i1p1f1_gn_201501-202012.nc"
    )
    assert first_file == expected_file


def test_inventory_get_file_urls():
    first_file = inv.get_file_urls([ds_id])[ds_id][0]

    expected_file = (
        "https://data.mips.copernicus-climate.eu/thredds/fileServer/esg_c3s-cmip6/"
        "CMIP6/ScenarioMIP/NCC/NorESM2-LM/ssp245/r1i1p1f1/Amon/"
        "hfss/gn/v20191108/hfss_Amon_NorESM2-LM_ssp245_r1i1p1f1_gn_201501-202012.nc"
    )
    assert first_file == expected_file


def teardown_module():
    pass
