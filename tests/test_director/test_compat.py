from rook.director import compat


def test_resultset_collects_https_uri():
    rs = compat.ResultSet()
    uri = "https://example.org/data.nc"

    rs.add("ds", [uri])

    assert rs.file_uris == [uri]


def test_is_characterised_returns_bool(monkeypatch):
    monkeypatch.setattr(compat, "_daops_is_characterised", lambda *a, **k: True)

    value = compat.is_characterised(["cmip6.CMIP.A.B.C.D.E.F.G"], require_all=True)

    assert isinstance(value, bool)


def test_is_characterised_fallback_when_daops_unavailable(monkeypatch):
    monkeypatch.setattr(compat, "_daops_is_characterised", None)

    assert compat.is_characterised(["cmip6.CMIP.A.B.C.D.E.F.G"], require_all=True) is False
