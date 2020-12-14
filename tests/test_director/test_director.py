from rook.director import Director


class TestDirector:

    collection = [
        "CMIP6.ScenarioMIP.CCCma.CanESM5.ssp370.r1i1p1f1.Amon.rsutcs.gn.v20190429"
    ]

    def test_1(self):
        inputs = {"time": "1886-01-01/1984-11-01"}
        d = Director(self.collection, inputs)
        assert d.project == "cmip6"
