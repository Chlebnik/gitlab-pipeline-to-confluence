"""Configuration settings loaded from config file, environment variables, and defaults.

Configuration priority (highest to lowest):
    1. Command line arguments
    2. Config file (YAML)
    3. Environment variables
    4. Default values

The application first loads defaults, then merges with environment variables,
then with config file (if provided), and finally with command line arguments.
"""

import os
import warnings
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv

load_dotenv()

DEFAULT_GITLAB_URL = "https://gitlab.example.com"
DEFAULT_CONFLUENCE_URL = "https://confluence.example.com"


def load_config_file(config_path: Optional[str]) -> dict[str, Any]:
    """Load configuration from a YAML file.

    Args:
        config_path: Path to the YAML config file. If None, returns empty dict.

    Returns:
        Dictionary containing configuration values from the file.

    Raises:
        FileNotFoundError: If the config file doesn't exist
        yaml.YAMLError: If the config file is invalid YAML
    """
    if not config_path:
        return {}

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def validate_config_keys(config: dict[str, Any], expected_keys: dict[str, list[str]]) -> None:
    """Log warnings for unknown keys in config file.

    Args:
        config: Loaded configuration dictionary
        expected_keys: Dict mapping section names to expected keys
                     e.g. {"gitlab": ["url", "token"], "confluence": ["url", "email", "token"]}
    """
    for section, keys in expected_keys.items():
        if section not in config:
            continue

        section_config = config[section]
        if not isinstance(section_config, dict):
            continue

        provided_keys = set(section_config.keys())
        expected = set(keys)
        unknown = provided_keys - expected

        if unknown:
            warnings.warn(
                f"Unknown key(s) in config '{section}': {sorted(unknown)}. "
                f"Expected: {sorted(expected)}. This may be a typo."
            )


def get_config_value(
    config: dict[str, Any],
    env_key: str,
    default: Any,
    nested_keys: list[str],
) -> Any:
    """Get a configuration value with priority: config file > env var > default.

    Priority order (highest to lowest):
        1. Config file
        2. Environment variable
        3. Default value

    Args:
        config: Configuration dictionary loaded from YAML file
        env_key: Environment variable name
        default: Default value if not found anywhere
        nested_keys: List of keys to navigate nested dict (e.g., ['gitlab', 'url'])

    Returns:
        The configuration value with highest priority
    """
    nested_config = config
    for key in nested_keys:
        if isinstance(nested_config, dict):
            nested_config = nested_config.get(key)
        else:
            break

    if nested_config is not None:
        return nested_config

    value = os.getenv(env_key)
    if value is not None:
        return value

    return default


def get_gitlab_url(config: Optional[dict[str, Any]] = None) -> str:
    """Get GitLab URL with priority: config file > env var > default."""
    config = config or {}
    return get_config_value(config, "GITLAB_URL", DEFAULT_GITLAB_URL, ["gitlab", "url"])


def get_gitlab_token(config: Optional[dict[str, Any]] = None) -> str:
    """Get GitLab token with priority: config file > env var > default."""
    config = config or {}
    return get_config_value(config, "GITLAB_TOKEN", "changeme", ["gitlab", "token"])


def get_confluence_url(config: Optional[dict[str, Any]] = None) -> str:
    """Get Confluence URL with priority: config file > env var > default."""
    config = config or {}
    return get_config_value(
        config, "CONFLUENCE_URL", DEFAULT_CONFLUENCE_URL, ["confluence", "url"]
    )


def get_confluence_email(config: Optional[dict[str, Any]] = None) -> str:
    """Get Confluence email with priority: config file > env var > default."""
    config = config or {}
    return get_config_value(
        config, "CONFLUENCE_EMAIL", "changeme", ["confluence", "email"]
    )


def get_confluence_token(config: Optional[dict[str, Any]] = None) -> str:
    """Get Confluence token with priority: config file > env var > default."""
    config = config or {}
    return get_config_value(
        config, "CONFLUENCE_TOKEN", "changeme", ["confluence", "token"]
    )


def get_history_count(config: Optional[dict[str, Any]] = None) -> int:
    """Get history count with priority: config file > env var > default."""
    config = config or {}
    value = get_config_value(config, "HISTORY_COUNT", 10, ["options", "history_count"])
    try:
        return int(value)
    except (ValueError, TypeError):
        return 10


GITLAB_TOKEN = os.getenv("GITLAB_TOKEN", "changeme")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL", "changeme")
CONFLUENCE_TOKEN = os.getenv("CONFLUENCE_TOKEN", "changeme")
GITLAB_URL = os.getenv("GITLAB_URL", DEFAULT_GITLAB_URL)
CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", DEFAULT_CONFLUENCE_URL)
DEFAULT_PROJECT_ID = os.getenv("PROJECT_ID", "")
DEFAULT_CONFLUENCE_PAGE_ID = os.getenv("CONFLUENCE_PAGE_ID", "")
