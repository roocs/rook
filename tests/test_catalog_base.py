from rook.catalog import base
from rook.catalog.base import Result


RECORDS = {
    "project.dataset": [
        "ScenarioMIP/Model/file_201501-210012.nc",
    ]
}


def test_result_files_uses_project_base_dir(monkeypatch):
    monkeypatch.setattr(
        base,
        "CONFIG",
        {"project:c3s-cmip6": {"base_dir": "/data/CMIP6"}},
    )

    result = Result("c3s-cmip6", RECORDS)

    assert result.files() == {
        "project.dataset": ["/data/CMIP6/ScenarioMIP/Model/file_201501-210012.nc"]
    }


def test_result_files_uses_global_s3_base_dir(monkeypatch):
    monkeypatch.setattr(
        base,
        "CONFIG",
        {
            "project:c3s-cmip6": {"base_dir": "/data/CMIP6"},
            "s3": {"base_dir": "s3://example-bucket/data/CMIP6"},
        },
    )

    result = Result("c3s-cmip6", RECORDS)

    assert result.files() == {
        "project.dataset": [
            "s3://example-bucket/data/CMIP6/ScenarioMIP/Model/file_201501-210012.nc"
        ]
    }


def test_result_files_uses_project_s3_base_dir_override(monkeypatch):
    monkeypatch.setattr(
        base,
        "CONFIG",
        {
            "project:c3s-cmip6": {
                "base_dir": "/data/CMIP6",
                "s3_base_dir": "s3://project-bucket/cmip6",
            },
            "s3": {"base_dir": "s3://global-bucket/data"},
        },
    )

    result = Result("c3s-cmip6", RECORDS)

    assert result.files() == {
        "project.dataset": [
            "s3://project-bucket/cmip6/ScenarioMIP/Model/file_201501-210012.nc"
        ]
    }


def test_result_download_urls_keep_data_node_root(monkeypatch):
    monkeypatch.setattr(
        base,
        "CONFIG",
        {
            "project:c3s-cmip6": {
                "base_dir": "/data/CMIP6",
                "data_node_root": "https://example.org/thredds/fileServer/cmip6",
            },
            "s3": {"base_dir": "s3://example-bucket/data/CMIP6"},
        },
    )

    result = Result("c3s-cmip6", RECORDS)

    assert result.download_urls() == {
        "project.dataset": [
            "https://example.org/thredds/fileServer/cmip6/ScenarioMIP/Model/file_201501-210012.nc"
        ]
    }
