"""
Unit tests for src.config — profile.yaml + env var unified configuration.

Precedence (lowest to highest):
    1. built-in code defaults
    2. profile.yaml (repo root, non-secret only)
    3. environment variables (DB_* / LLM_*)

Also enforces acceptance red lines:
    - profile.yaml must not contain secret keys (password/api_key/secret/token)
    - .env.example must only contain placeholder values
"""
import yaml
import pytest

from src import config as config_module
from src.config import (
    REPO_ROOT, PROFILE_FILE,
    get_database_config, get_llm_config,
)

_ENV_DB = [
    "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD",
    "DB_POOL_MIN", "DB_POOL_MAX",
]
_ENV_LLM = ["LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL", "LLM_TEMPERATURE"]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Make config tests hermetic: remove all DB_* / LLM_* env vars."""
    for name in _ENV_DB + _ENV_LLM:
        monkeypatch.delenv(name, raising=False)
    yield


def _keys(obj):
    """Collect all dict keys in a nested structure (lowercased)."""
    keys = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            keys.add(str(k).lower())
            keys |= _keys(v)
    elif isinstance(obj, list):
        for item in obj:
            keys |= _keys(item)
    return keys


def test_defaults_when_profile_missing(tmp_path):
    cfg = config_module._load(profile_file=tmp_path / "nope.yaml")
    assert cfg["database"] == {
        "host": "localhost", "port": 5432, "name": "unires",
        "user": "unires", "password": "demo123",
        "pool_min": 1, "pool_max": 10,
    }
    assert cfg["llm"]["base_url"] == "http://127.0.0.1:8080/v1"
    assert cfg["llm"]["api_key"] == "fake-key"
    assert cfg["llm"]["model"] == "qwen3-coder-80b"
    assert cfg["llm"]["temperature"] == 0.1


def test_profile_yaml_merges_over_defaults(tmp_path):
    profile = tmp_path / "p.yaml"
    profile.write_text(yaml.safe_dump({
        "database": {"host": "db.example", "port": 5435, "pool_min": 2},
        "llm": {"model": "test-model"},
    }), encoding="utf-8")
    cfg = config_module._load(profile_file=profile)
    assert cfg["database"]["host"] == "db.example"
    assert cfg["database"]["port"] == 5435
    assert cfg["database"]["pool_min"] == 2
    assert cfg["database"]["pool_max"] == 10
    assert cfg["database"]["name"] == "unires"          # untouched key
    assert cfg["llm"]["model"] == "test-model"
    assert cfg["llm"]["base_url"] == "http://127.0.0.1:8080/v1"  # untouched


def test_env_overrides_profile_yaml(tmp_path, monkeypatch):
    profile = tmp_path / "p.yaml"
    profile.write_text(yaml.safe_dump({
        "database": {"host": "db.example", "port": 5435},
        "llm": {"base_url": "http://from-yaml", "model": "model-from-yaml"},
    }), encoding="utf-8")
    monkeypatch.setenv("DB_HOST", "db.from-env")
    monkeypatch.setenv("DB_PORT", "6543")
    monkeypatch.setenv("DB_PASSWORD", "secret-from-env")
    monkeypatch.setenv("DB_POOL_MIN", "3")
    monkeypatch.setenv("DB_POOL_MAX", "12")
    monkeypatch.setenv("LLM_BASE_URL", "http://from-env")
    monkeypatch.setenv("LLM_API_KEY", "key-from-env")
    cfg = config_module._load(profile_file=profile)
    assert cfg["database"]["host"] == "db.from-env"
    assert cfg["database"]["port"] == 6543
    assert cfg["database"]["password"] == "secret-from-env"
    assert cfg["database"]["pool_min"] == 3
    assert cfg["database"]["pool_max"] == 12
    assert cfg["llm"]["base_url"] == "http://from-env"
    assert cfg["llm"]["api_key"] == "key-from-env"


def test_llm_temperature_is_float(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_TEMPERATURE", "0.25")
    cfg = config_module._load(profile_file=tmp_path / "nope.yaml")
    assert isinstance(cfg["llm"]["temperature"], float)
    assert cfg["llm"]["temperature"] == 0.25


@pytest.mark.parametrize("profile_text, expected", [
    ("database:\n  password: yaml-secret\n", "database.password"),
    ("llm:\n  api_key: yaml-key\n", "llm.api_key"),
    ("database:\n  surprise: value\n", "database.surprise"),
    ("unknown:\n  value: 1\n", "unknown section"),
])
def test_profile_yaml_rejects_secret_and_unknown_keys(tmp_path, profile_text, expected):
    profile = tmp_path / "p.yaml"
    profile.write_text(profile_text, encoding="utf-8")
    with pytest.raises(RuntimeError, match=expected):
        config_module._load(profile_file=profile)


def test_profile_yaml_rejects_non_mapping_root(tmp_path):
    profile = tmp_path / "p.yaml"
    profile.write_text("- not\n- mapping\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="root must be a mapping"):
        config_module._load(profile_file=profile)


def test_invalid_port_raises_runtime_error(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PORT", "not-an-int")
    with pytest.raises(RuntimeError, match="DB_PORT must be an integer"):
        config_module._load(profile_file=tmp_path / "nope.yaml")


@pytest.mark.parametrize("env_name,value,expected", [
    ("DB_POOL_MIN", "not-int", "DB_POOL_MIN must be an integer"),
    ("DB_POOL_MAX", "not-int", "DB_POOL_MAX must be an integer"),
    ("DB_POOL_MIN", "0", "DB_POOL_MIN must be >= 1"),
    ("DB_POOL_MAX", "0", "DB_POOL_MAX must be >= pool_min"),
    ("DB_POOL_MAX", "51", "DB_POOL_MAX must be <= 50"),
])
def test_invalid_pool_config_raises_runtime_error(tmp_path, monkeypatch,
                                                 env_name, value, expected):
    monkeypatch.setenv(env_name, value)
    with pytest.raises(RuntimeError, match=expected):
        config_module._load(profile_file=tmp_path / "nope.yaml")


def test_invalid_temperature_raises_runtime_error(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_TEMPERATURE", "hot")
    with pytest.raises(RuntimeError, match="LLM_TEMPERATURE must be a number"):
        config_module._load(profile_file=tmp_path / "nope.yaml")


def test_get_database_config_shape():
    cfg = get_database_config()
    assert set(cfg) == {
        "host", "port", "name", "user", "password", "pool_min", "pool_max",
    }


def test_get_llm_config_shape():
    cfg = get_llm_config()
    assert set(cfg) == {"base_url", "api_key", "model", "temperature"}
    assert isinstance(cfg["temperature"], float)


def test_get_config_returns_copy():
    db1 = get_database_config()
    db1["host"] = "mutated"
    assert get_database_config()["host"] != "mutated"


def test_profile_yaml_contains_no_secret_keys():
    if not PROFILE_FILE.exists():
        pytest.skip("profile.yaml not present")
    raw = yaml.safe_load(PROFILE_FILE.read_text(encoding="utf-8")) or {}
    secret_keys = _keys(raw) & {"password", "api_key", "secret", "token"}
    assert not secret_keys, f"profile.yaml leaked secret keys: {secret_keys}"


def test_env_example_documents_required_secrets_without_real_values():
    example = REPO_ROOT / ".env.example"
    text = example.read_text(encoding="utf-8")
    for key in ("DB_PASSWORD", "LLM_API_KEY", "JWT_SECRET"):
        assert key in text, f".env.example must document {key}"
    assert "SECRET_KEY=" not in text


def test_env_example_active_values_do_not_override_non_secret_profile_values():
    example = REPO_ROOT / ".env.example"
    active_entries = {}
    for line in example.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        active_entries[key] = value

    assert set(active_entries) == {"DB_PASSWORD", "LLM_API_KEY", "JWT_SECRET"}
    assert all(value == "" for value in active_entries.values())
