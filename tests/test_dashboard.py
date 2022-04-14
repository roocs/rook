import pytest

from rook.dashboard import Dashboard


@pytest.mark.xfail(reason="remote test data might not be available")
def test_dashboard(tmpdir):
    dash = Dashboard(output_dir=tmpdir)
    dash.load(
        "http://rook4.cloud.dkrz.de/outputs/rook/64413a5a-bbda-11ec-9cfa-fa163ed6c06f/wps_requests.csv",
        filter="orchestrate",
    )
    dash.load_downloads(
        "http://rook4.cloud.dkrz.de/outputs/rook/64413a5a-bbda-11ec-9cfa-fa163ed6c06f/downloads.csv"
    )
    print(dash.write())
    # assert False
