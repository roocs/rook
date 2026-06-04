from rook.director import compat


def test_resultset_collects_https_uri():
    rs = compat.ResultSet()
    uri = "https://example.org/data.nc"

    rs.add("ds", [uri])

    assert rs.file_uris == [uri]


def test_is_characterised_returns_bool():
    value = compat.is_characterised(["cmip6.CMIP.A.B.C.D.E.F.G"], require_all=True)

    assert isinstance(value, bool)


def test_is_characterised_returns_false():
    assert compat.is_characterised(["cmip6.CMIP.A.B.C.D.E.F.G"], require_all=True) is False
