from rook.catalog import DBCatalog

C3S_CMIP6_DAY_COLLECTION = (
    "c3s-cmip6.CMIP.SNU.SAM0-UNICON.historical.r1i1p1f1.day.pr.gn.v20190323"
)
C3S_CMIP6_MON_COLLECTION = (
    "c3s-cmip6.ScenarioMIP.INM.INM-CM5-0.ssp245.r1i1p1f1.Amon.rlds.gr1.v20190619"
)
C3S_CMIP6_FX_COLLECTION = (
    "c3s-cmip6.ScenarioMIP.MRI.MRI-ESM2-0.ssp370.r1i1p1f1.fx.orog.gn.v20190603"
)

C3S_ATLAS_V2_CMIP6_COLLECTION = "c3s-cica-atlas.sst.CMIP6.ssp245.mon.v2"


def test_db_catalog_c3s_cmip6_mon(stratus):
    cat = DBCatalog(project="c3s-cmip6")
    cat.to_db()
    result = cat.search(collection=C3S_CMIP6_MON_COLLECTION)
    assert result.matches == 1
    files = result.files()[C3S_CMIP6_MON_COLLECTION]
    assert len(files) == 1
    # check download url
    urls = result.download_urls()[C3S_CMIP6_MON_COLLECTION]
    expected_url = (
        "https://data.mips.climate.copernicus.eu/thredds/fileServer/esg_c3s-cmip6/"
        "ScenarioMIP/INM/INM-CM5-0/ssp245/r1i1p1f1/Amon/rlds/gr1/v20190619/"
        "rlds_Amon_INM-CM5-0_ssp245_r1i1p1f1_gr1_201501-210012.nc"
    )
    assert expected_url == urls[0]


def test_db_catalog_c3s_cmip6_day():
    cat = DBCatalog(project="c3s-cmip6")
    # all files
    result = cat.search(collection=C3S_CMIP6_DAY_COLLECTION)
    assert result.matches == 1
    files = result.files()[C3S_CMIP6_DAY_COLLECTION]
    assert len(files) == 165
    # one year only
    result = cat.search(
        collection=C3S_CMIP6_DAY_COLLECTION,
        time="1900-01-01/1900-12-31",
    )
    assert result.matches == 1
    files = result.files()[C3S_CMIP6_DAY_COLLECTION]
    assert len(files) == 1
    assert "CMIP/SNU/SAM0-UNICON/historical/r1i1p1f1/day/pr/gn/v20190323" in files[0]
    assert "pr_day_SAM0-UNICON_historical_r1i1p1f1_gn_19000101-19001231.nc" in files[0]


def test_db_catalog_c3s_cmip6_fx():
    cat = DBCatalog(project="c3s-cmip6")
    result = cat.search(collection=C3S_CMIP6_FX_COLLECTION)
    # all files
    assert result.matches == 1
    files = result.files()[C3S_CMIP6_FX_COLLECTION]
    assert len(files) == 1
    assert "ScenarioMIP/MRI/MRI-ESM2-0/ssp370/r1i1p1f1/fx/orog/gn/v20190603" in files[0]
    assert "orog_fx_MRI-ESM2-0_ssp370_r1i1p1f1_gn.nc" in files[0]
    # filter by time should have no effect ... to time axis
    result = cat.search(
        collection=C3S_CMIP6_FX_COLLECTION,
        time="2000-01-01/2010-12-31",
    )
    assert result.matches == 1
    files = result.files()[C3S_CMIP6_FX_COLLECTION]
    assert len(files) == 1


def test_db_catalog_c3s_cmip6_multiple():
    cat = DBCatalog(project="c3s-cmip6")
    result = cat.search(collection=[C3S_CMIP6_MON_COLLECTION, C3S_CMIP6_FX_COLLECTION])
    assert result.matches == 2
    files = result.files()[C3S_CMIP6_MON_COLLECTION]
    assert len(files) == 1
    files = result.files()[C3S_CMIP6_FX_COLLECTION]
    assert len(files) == 1


def test_db_catalog_c3s_cica_atlas():
    cat = DBCatalog(project="c3s-cica-atlas")
    # all files
    result = cat.search(collection=C3S_ATLAS_V2_CMIP6_COLLECTION)
    assert result.matches == 1
    files = result.files()[C3S_ATLAS_V2_CMIP6_COLLECTION]
    # print(files)
    assert len(files) == 1
    assert "CMIP6/ssp245/sst_CMIP6_ssp245_mon_201501-210012_v02.nc" in files[0]
