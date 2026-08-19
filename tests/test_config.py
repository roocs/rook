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


def test_get_fix_backend_defaults_to_woodpecker(monkeypatch):
    monkeypatch.setattr(config, "_CONFIG", {})

    assert config.get_fix_backend() == "woodpecker"


def test_get_fix_backend_uses_fixes_config(monkeypatch):
    monkeypatch.setattr(config, "_CONFIG", {"fixes": {"backend": "woodpecker"}})

    assert config.get_fix_backend() == "woodpecker"


def test_get_fix_backend_rejects_unknown_backend(monkeypatch):
    monkeypatch.setattr(config, "_CONFIG", {"fixes": {"backend": "unknown"}})

    with pytest.raises(config.ConfigurationError, match=r"fixes\.backend"):
        config.get_fix_backend()


def test_batching_uses_timestep_defaults(monkeypatch):
    monkeypatch.setattr(config, "_CONFIG", {})

    assert config.get_batching_config() == {
        "target_timesteps": 2000,
        "min_batch_years": 1,
        "max_batch_years": 10,
    }


def test_concat_batching_uses_independent_conservative_defaults(monkeypatch):
    monkeypatch.setattr(config, "_CONFIG", {})

    assert config.get_concat_batching_config() == {
        "target_timesteps": 365,
        "min_batch_years": 1,
        "max_batch_years": 1,
    }


def test_batching_uses_existing_config_override(monkeypatch):
    monkeypatch.setattr(
        config,
        "_CONFIG",
        {
            "subset:batching": {
                "target_timesteps": "1000",
                "min_batch_years": "2",
                "max_batch_years": "4",
            }
        },
    )

    assert config.get_batching_config() == {
        "target_timesteps": 1000,
        "min_batch_years": 2,
        "max_batch_years": 4,
    }


def test_concat_batching_can_be_configured_independently(monkeypatch):
    monkeypatch.setattr(
        config,
        "_CONFIG",
        {
            "subset:batching": {"target_timesteps": "1000"},
            "concat:batching": {
                "target_timesteps": "180",
                "min_batch_years": "1",
                "max_batch_years": "1",
            },
        },
    )

    assert config.get_concat_batching_config() == {
        "target_timesteps": 180,
        "min_batch_years": 1,
        "max_batch_years": 1,
    }
    assert config.get_batching_config() == {
        "target_timesteps": 1000,
        "min_batch_years": 1,
        "max_batch_years": 10,
    }


def test_diagnostic_free_memory_defaults_to_false(monkeypatch):
    monkeypatch.setattr(config, "_CONFIG", {})
    monkeypatch.delenv("ROOK_DIAGNOSTIC_MALLOC_TRIM", raising=False)

    assert config.get_diagnostic_free_memory() is False


def test_diagnostic_free_memory_uses_general_section(monkeypatch):
    monkeypatch.setattr(
        config,
        "_CONFIG",
        {"diagnostics": {"free_memory": "true"}},
    )
    monkeypatch.delenv("ROOK_DIAGNOSTIC_MALLOC_TRIM", raising=False)

    assert config.get_diagnostic_free_memory() is True


def test_diagnostic_free_memory_environment_overrides_config(monkeypatch):
    monkeypatch.setattr(
        config,
        "_CONFIG",
        {"diagnostics": {"free_memory": "false"}},
    )
    monkeypatch.setenv("ROOK_DIAGNOSTIC_MALLOC_TRIM", "true")

    assert config.get_diagnostic_free_memory() is True


@pytest.mark.parametrize("value", [0, -1, 2.5, True, "invalid"])
def test_batching_requires_positive_integers(monkeypatch, value):
    monkeypatch.setattr(
        config,
        "_CONFIG",
        {"subset:batching": {"target_timesteps": value}},
    )

    with pytest.raises(
        config.ConfigurationError, match=r"subset:batching\.target_timesteps"
    ):
        config.get_batching_config()


def test_batching_rejects_inverted_year_bounds(monkeypatch):
    monkeypatch.setattr(
        config,
        "_CONFIG",
        {
            "subset:batching": {
                "min_batch_years": "5",
                "max_batch_years": "2",
            }
        },
    )

    with pytest.raises(config.ConfigurationError, match="min_batch_years"):
        config.get_batching_config()


def test_subset_batch_output_uses_defaults_and_clisops_size_limit(monkeypatch):
    monkeypatch.setattr(
        config,
        "_CONFIG",
        {"clisops:write": {"file_size_limit": "2GB"}},
    )

    assert config.get_subset_batch_output_config() == {
        "merge_outputs": True,
        "merge_target_bytes": 200_000_000,
        "max_output_bytes": 2_000_000_000,
    }


def test_subset_batch_output_can_be_overridden(monkeypatch):
    monkeypatch.setattr(
        config,
        "_CONFIG",
        {
            "clisops:write": {"file_size_limit": "500MB"},
            "subset:batching": {
                "merge_outputs": "false",
                "merge_target_size": "100MB",
            },
        },
    )

    assert config.get_subset_batch_output_config() == {
        "merge_outputs": False,
        "merge_target_bytes": 100_000_000,
        "max_output_bytes": 500_000_000,
    }


@pytest.mark.parametrize("value", ["invalid", "0MB"])
def test_subset_batch_output_rejects_invalid_merge_target(monkeypatch, value):
    monkeypatch.setattr(
        config,
        "_CONFIG",
        {"subset:batching": {"merge_target_size": value}},
    )

    with pytest.raises(config.ConfigurationError, match="merge_target_size"):
        config.get_subset_batch_output_config()


def test_subset_batch_output_target_is_capped_by_clisops_limit(monkeypatch):
    monkeypatch.setattr(
        config,
        "_CONFIG",
        {
            "clisops:write": {"file_size_limit": "100MB"},
            "subset:batching": {"merge_target_size": "200MB"},
        },
    )

    assert config.get_subset_batch_output_config()["merge_target_bytes"] == 100_000_000


def test_subset_batch_output_rejects_zero_clisops_limit(monkeypatch):
    monkeypatch.setattr(
        config,
        "_CONFIG",
        {"clisops:write": {"file_size_limit": "0MB"}},
    )

    with pytest.raises(config.ConfigurationError, match="file_size_limit"):
        config.get_subset_batch_output_config()


def test_health_readable_files_default_to_empty(monkeypatch):
    monkeypatch.setattr(config, "_CONFIG", {})

    assert config.get_health_readable_files() == {}


def test_health_readable_files_use_project_base_dirs(monkeypatch):
    monkeypatch.setattr(
        config,
        "_CONFIG",
        {
            "health": {"projects": "c3s-cordex, c3s-cica-atlas"},
            "project:c3s-cordex": {"base_dir": "/data/c3s-cordex"},
            "project:c3s-cica-atlas": {"base_dir": "/data/c3s-cica-atlas"},
        },
    )

    assert config.get_health_readable_files() == {
        "c3s-cordex": "/data/c3s-cordex/.health-check.txt",
        "c3s-cica-atlas": "/data/c3s-cica-atlas/.health-check.txt",
    }


@pytest.mark.parametrize(
    "value",
    [123, "c3s-cordex,", ",c3s-cordex"],
)
def test_health_readable_files_reject_invalid_config(monkeypatch, value):
    monkeypatch.setattr(
        config,
        "_CONFIG",
        {"health": {"projects": value}},
    )

    with pytest.raises(config.ConfigurationError, match=r"health\.projects"):
        config.get_health_readable_files()


def test_health_readable_files_require_project_base_dir(monkeypatch):
    monkeypatch.setattr(
        config,
        "_CONFIG",
        {"health": {"projects": "c3s-cordex"}},
    )

    with pytest.raises(config.ConfigurationError, match=r"c3s-cordex.*base_dir"):
        config.get_health_readable_files()


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
