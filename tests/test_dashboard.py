from rook.dashboard import Dashboard


def test_dashboard(tmpdir):
    dash = Dashboard(output_dir=tmpdir)
    dash.load(
        "http://rook3.cloud.dkrz.de:80/outputs/rook/9963ecd6-cde8-11eb-bb2b-fa163e466023/wps_requests.csv",
        filter="orchestrate",
    )
    print(dash.write())
    # assert False
