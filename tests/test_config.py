import rook
from rook import config


def test_rook_has_no_config_compatibility_alias():
    assert not hasattr(rook, "CONFIG")


def test_get_project_config(monkeypatch):
    monkeypatch.setattr(
        config,
        "_CONFIG",
        {"project:demo": {"base_dir": "/data/demo"}},
    )

    assert config.get_project_config("demo") == {"base_dir": "/data/demo"}
    assert config.get_project_config("missing") == {}


def test_get_storage_base_prefers_project_s3_override(monkeypatch):
    monkeypatch.setattr(
        config,
        "_CONFIG",
        {
            "project:demo": {
                "base_dir": "/data/demo",
                "s3_base_dir": "s3://project/demo",
            },
            "s3": {"base_dir": "s3://global/data"},
        },
    )

    assert config.get_storage_base("demo") == "s3://project/demo"


def test_get_storage_base_falls_back_to_local_project_root(monkeypatch):
    monkeypatch.setattr(
        config,
        "_CONFIG",
        {"project:demo": {"base_dir": "/data/demo"}},
    )

    assert config.get_storage_base("demo") == "/data/demo"


def test_s3_options_ignore_malformed_optional_json(monkeypatch):
    monkeypatch.setattr(
        config,
        "_CONFIG",
        {"s3": {"storage_options_json": "not-json", "anon": "false"}},
    )

    assert config.get_s3_storage_options() == {"anon": False}


def test_reload_config_updates_current_config(monkeypatch):
    reloaded = {"project:demo": {"base_dir": "/new/data"}}
    monkeypatch.setattr(config, "_CONFIG", config.get_config())
    monkeypatch.setattr(config, "_reload_clisops_config", lambda _path: reloaded)

    assert config.reload_config() is reloaded
    assert config.get_config() is reloaded
