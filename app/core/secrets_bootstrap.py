"""Utilities for bootstrapping Streamlit secrets from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from app.core.logging import get_logger

logger = get_logger(__name__)

# Supported environment variable names for required auth keys.
_AUTH_ENV_KEYS: dict[str, tuple[str, ...]] = {
    "client_id": ("STREAMLIT_AUTH__CLIENT_ID", "STREAMLIT_AUTH_CLIENT_ID"),
    "client_secret": ("STREAMLIT_AUTH__CLIENT_SECRET", "STREAMLIT_AUTH_CLIENT_SECRET"),
    "cookie_secret": ("STREAMLIT_AUTH__COOKIE_SECRET", "STREAMLIT_AUTH_COOKIE_SECRET"),
    "redirect_uri": ("STREAMLIT_AUTH__REDIRECT_URI", "STREAMLIT_AUTH_REDIRECT_URI"),
    "server_metadata_url": (
        "STREAMLIT_AUTH__SERVER_METADATA_URL",
        "STREAMLIT_AUTH_SERVER_METADATA_URL",
    ),
}

_GENERAL_ENV_KEYS: dict[str, tuple[str, ...]] = {
    "debug": ("STREAMLIT_GENERAL__DEBUG", "STREAMLIT_GENERAL_DEBUG"),
    "enable_mock_auth": (
        "STREAMLIT_GENERAL__ENABLE_MOCK_AUTH",
        "STREAMLIT_GENERAL_ENABLE_MOCK_AUTH",
    ),
}


def _resolve_env_value(names: tuple[str, ...]) -> str | None:
    """Return the first non-empty environment variable value from names."""
    for env_name in names:
        value = os.getenv(env_name)
        if value not in (None, ""):
            return value
    return None


def ensure_streamlit_secrets_file() -> None:
    """Create `.streamlit/secrets.toml` from environment variables if missing."""
    root_dir = Path(__file__).resolve().parents[2]
    secrets_path = root_dir / ".streamlit" / "secrets.toml"

    if secrets_path.exists():
        return

    auth_values: dict[str, str] = {}
    for key, env_names in _AUTH_ENV_KEYS.items():
        value = _resolve_env_value(env_names)
        if value is not None:
            auth_values[key] = value

    missing = [key for key in _AUTH_ENV_KEYS if key not in auth_values]
    if missing:
        logger.warning(
            "Unable to bootstrap Streamlit secrets file from environment",
            missing_auth_keys=sorted(missing),
        )
        return

    general_values: dict[str, str] = {}
    for key, env_names in _GENERAL_ENV_KEYS.items():
        value = _resolve_env_value(env_names)
        if value is not None:
            general_values[key] = value.lower() if value.lower() in {"true", "false"} else value

    secrets_lines = ["[auth]"]
    for key, value in auth_values.items():
        escaped = value.replace("\"", "\\\"")
        secrets_lines.append(f'{key} = "{escaped}"')

    if general_values:
        secrets_lines.append("")
        secrets_lines.append("[general]")
        for key, value in general_values.items():
            if value in {"true", "false"}:
                secrets_lines.append(f"{key} = {value}")
            else:
                escaped = value.replace("\"", "\\\"")
                secrets_lines.append(f'{key} = "{escaped}"')

    secrets_content = "\n".join(secrets_lines) + "\n"

    secrets_path.parent.mkdir(parents=True, exist_ok=True)
    secrets_path.write_text(secrets_content, encoding="utf-8")
    logger.info(
        "Bootstrapped Streamlit secrets file from environment variables",
        secrets_path=str(secrets_path),
        auth_keys=sorted(auth_values.keys()),
    )
