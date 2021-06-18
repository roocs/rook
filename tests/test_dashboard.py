import pytest

from rook.dashboard import Dashboard


@pytest.mark.xfail(reason="remote test data might not be available")
def test_dashboard(tmpdir):
    dash = Dashboard(output_dir=tmpdir)
    dash.load(
        "http://rook4.cloud.dkrz.de:80/outputs/rook/9e3ae300-d044-11eb-8ce3-fa163e1098db/wps_requests.csv",
        filter="orchestrate",
    )
    print(dash.write())
    # assert False
