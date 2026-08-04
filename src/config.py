"""
Unified configuration loader for Uni-Resource Agent.

Precedence (lowest to highest):
    1. built-in code defaults
    2. ``profile.yaml`` (repo root, non-secret defaults only)
    3. environment variables ``DB_*`` / ``LLM_*`` (loaded from ``.env`` when
       present; real shell env always wins)

Consumers:
    - ``src/db/database.py`` -> ``get_database_config()``
    - ``src/agents/agent.py`` -> ``get_llm_config()``
    - ``src/models/llm_client.py`` (deprecated) -> ``get_llm_config()``

Secrets (DB password, LLM api key) must be supplied via environment
variables / ``.env``; ``profile.yaml`` must never contain them.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

import yaml
from dotenv import load_dotenv

from src.logging_config import get_logger

logger = get_logger("config")

REPO_ROOT = Path(__file__).resolve().parent.parent
PROFILE_FILE = REPO_ROOT / "profile.yaml"
ENV_FILE = REPO_ROOT / ".env"

_ALLOWED_PROFILE_KEYS = {
    "database": {"host", "port", "name", "user", "pool_min", "pool_max"},
    "llm": {"base_url", "model", "temperature"},
}

_SECRET_KEYS = {"password", "api_key", "secret", "token", "jwt_secret"}

_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "unires",
        "user": "unires",
        "password": "demo123",
        "pool_min": 1,
        "pool_max": 10,
    },
    "llm": {
        "base_url": "http://127.0.0.1:8080/v1",
        "api_key": "fake-key",
        "model": "qwen3-coder-80b",
        "temperature": 0.1,
    },
}

_ENV_MAP: Dict[str, Dict[str, str]] = {
    "database": {
        "host": "DB_HOST",
        "port": "DB_PORT",
        "name": "DB_NAME",
        "user": "DB_USER",
        "password": "DB_PASSWORD",
        "pool_min": "DB_POOL_MIN",
        "pool_max": "DB_POOL_MAX",
    },
    "llm": {
        "base_url": "LLM_BASE_URL",
        "api_key": "LLM_API_KEY",
        "model": "LLM_MODEL",
        "temperature": "LLM_TEMPERATURE",
    },
}


def _load(profile_file: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """Build the merged config dict. ``profile_file`` is injectable for tests."""
    target = profile_file or PROFILE_FILE
    config = {section: dict(values) for section, values in _DEFAULTS.items()}

    if target.exists():
        try:
            raw = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise RuntimeError(f"Failed to parse profile file {target}: {exc}") from exc
        if not isinstance(raw, dict):
            raise RuntimeError(f"{target} root must be a mapping")
        for section, section_data in raw.items():
            if section not in _ALLOWED_PROFILE_KEYS:
                raise RuntimeError(f"{target}: unknown section {section!r}")
            if not isinstance(section_data, dict):
                raise RuntimeError(f"{target}: section {section!r} must be a mapping")
            for key, value in section_data.items():
                if not isinstance(key, str):
                    raise RuntimeError(f"{target}: invalid key type in section {section!r}")
                if key in _SECRET_KEYS:
                    raise RuntimeError(f"{target}: secret key {section}.{key} is not allowed")
                if key not in _ALLOWED_PROFILE_KEYS[section]:
                    raise RuntimeError(f"{target}: {section}.{key} is not allowed")
                if value is not None:
                    config[section][key] = value
    else:
        logger.warning("profile file %s not found, using built-in defaults", target)

    for section, mapping in _ENV_MAP.items():
        for key, env_name in mapping.items():
            value = os.getenv(env_name)
            if value not in (None, ""):
                config[section][key] = value

    try:
        config["database"]["port"] = int(config["database"]["port"])
    except (TypeError, ValueError) as exc:
        raise RuntimeError("database.port/DB_PORT must be an integer") from exc

    for key, env_name in (("pool_min", "DB_POOL_MIN"), ("pool_max", "DB_POOL_MAX")):
        try:
            config["database"][key] = int(config["database"][key])
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"database.{key}/{env_name} must be an integer") from exc
    pool_min = config["database"]["pool_min"]
    pool_max = config["database"]["pool_max"]
    if pool_min < 1:
        raise RuntimeError("database.pool_min/DB_POOL_MIN must be >= 1")
    if pool_max < pool_min:
        raise RuntimeError("database.pool_max/DB_POOL_MAX must be >= pool_min")
    if pool_max > 50:
        raise RuntimeError("database.pool_max/DB_POOL_MAX must be <= 50")

    try:
        config["llm"]["temperature"] = float(config["llm"]["temperature"])
    except (TypeError, ValueError) as exc:
        raise RuntimeError("llm.temperature/LLM_TEMPERATURE must be a number") from exc
    return config


load_dotenv(ENV_FILE, override=False)

_config = _load()


def get_database_config() -> Dict[str, Any]:
    """Return merged database config including pool_min/pool_max."""
    return dict(_config["database"])


def get_llm_config() -> Dict[str, Any]:
    """Return merged LLM config. Keys: base_url, api_key, model, temperature."""
    return dict(_config["llm"])
