import pytest

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


def test_get_fix_backend_defaults_to_legacy(monkeypatch):
    monkeypatch.setattr(config, "_CONFIG", {})

    assert config.get_fix_backend() == "legacy"


def test_get_fix_backend_uses_fixes_config(monkeypatch):
    monkeypatch.setattr(config, "_CONFIG", {"fixes": {"backend": "woodpecker"}})

    assert config.get_fix_backend() == "woodpecker"


def test_get_fix_backend_rejects_unknown_backend(monkeypatch):
    monkeypatch.setattr(config, "_CONFIG", {"fixes": {"backend": "unknown"}})

    with pytest.raises(config.ConfigurationError, match=r"fixes\.backend"):
        config.get_fix_backend()


def test_s3_options_reject_malformed_optional_json_without_exposing_value(monkeypatch):
    malformed_value = "not-json-private-value"
    monkeypatch.setattr(
        config,
        "_CONFIG",
        {"s3": {"storage_options_json": malformed_value}},
    )

    with pytest.raises(config.ConfigurationError) as exc_info:
        config.get_s3_storage_options()

    assert "storage_options_json" in str(exc_info.value)
    assert malformed_value not in str(exc_info.value)


@pytest.mark.parametrize(
    "s3_config, option",
    [
        ({"storage_options_json": "[]"}, "storage_options_json"),
        ({"client_kwargs_json": "[]"}, "client_kwargs_json"),
        ({"anon": "sometimes"}, "anon"),
        (
            {"storage_options_json": '{"client_kwargs": "invalid"}'},
            "client_kwargs",
        ),
    ],
)
def test_s3_options_reject_invalid_types(monkeypatch, s3_config, option):
    monkeypatch.setattr(config, "_CONFIG", {"s3": s3_config})

    with pytest.raises(config.ConfigurationError, match=option):
        config.get_s3_storage_options()


def test_s3_options_merge_valid_structured_options(monkeypatch):
    monkeypatch.setattr(
        config,
        "_CONFIG",
        {
            "s3": {
                "storage_options_json": '{"anon": true, "client_kwargs": {"region_name": "eu-west-1"}}',
                "client_kwargs_json": '{"use_ssl": false}',
                "endpoint_url": "https://s3.example.org",
            }
        },
    )

    assert config.get_s3_storage_options() == {
        "anon": True,
        "client_kwargs": {
            "region_name": "eu-west-1",
            "use_ssl": False,
            "endpoint_url": "https://s3.example.org",
        },
    }


def test_project_config_rejects_malformed_section(monkeypatch):
    monkeypatch.setattr(config, "_CONFIG", {"project:demo": "invalid"})

    with pytest.raises(config.ConfigurationError, match=r"\[project:demo\]"):
        config.get_project_config("demo")


def test_reload_config_updates_current_config(monkeypatch):
    reloaded = {"project:demo": {"base_dir": "/new/data"}}
    monkeypatch.setattr(config, "_CONFIG", config.get_config())
    monkeypatch.setattr(config, "_reload_clisops_config", lambda _path: reloaded)

    assert config.reload_config() is reloaded
    assert config.get_config() is reloaded
