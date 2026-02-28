"""Unit tests for config module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

import config


class TestLoadConfigFile:
    """Tests for load_config_file function."""

    def test_load_config_file_none(self):
        """Test loading config with None path."""
        result = config.load_config_file(None)

        assert result == {}

    def test_load_config_file_not_found(self):
        """Test loading non-existent config file."""
        with pytest.raises(FileNotFoundError):
            config.load_config_file("/nonexistent/path/config.yaml")

    def test_load_config_file_valid(self):
        """Test loading valid config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
                {
                    "gitlab": {"url": "https://custom.gitlab.com", "token": "secret"},
                    "confluence": {"url": "https://custom.confluence.com"},
                },
                f,
            )
            temp_path = f.name

        try:
            result = config.load_config_file(temp_path)

            assert result["gitlab"]["url"] == "https://custom.gitlab.com"
            assert result["gitlab"]["token"] == "secret"
            assert result["confluence"]["url"] == "https://custom.confluence.com"
        finally:
            os.unlink(temp_path)

    def test_load_config_file_empty(self):
        """Test loading empty config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            result = config.load_config_file(temp_path)

            assert result == {}
        finally:
            os.unlink(temp_path)


class TestGetConfigValue:
    """Tests for get_config_value function."""

    def test_get_config_value_from_env(self):
        """Test getting value from environment variable."""
        with patch.dict(os.environ, {"TEST_VAR": "env_value"}):
            result = config.get_config_value({}, "TEST_VAR", "default", ["nested"])

            assert result == "env_value"

    def test_get_config_value_from_file(self):
        """Test getting value from config file."""
        with patch.dict(os.environ, {}, clear=True):
            file_config = {"nested": {"key": "file_value"}}

            result = config.get_config_value(file_config, "TEST_VAR", "default", ["nested", "key"])

            assert result == "file_value"

    def test_get_config_value_default(self):
        """Test getting default value."""
        with patch.dict(os.environ, {}, clear=True):
            result = config.get_config_value({}, "TEST_VAR", "default_value", ["nested"])

            assert result == "default_value"

    def test_get_config_value_file_overrides_env(self):
        """Test that config file overrides environment variable.

        Priority: config file > env var > default
        """
        with patch.dict(os.environ, {"TEST_VAR": "env_value"}):
            file_config = {"nested": {"key": "file_value"}}

            result = config.get_config_value(file_config, "TEST_VAR", "default", ["nested", "key"])

            assert result == "file_value"


class TestConfigPriority:
    """Tests for correct config priority order (config file > env var > default)."""

    def test_config_file_overrides_env_var(self):
        """Config file values should override environment variables."""
        with patch.dict(os.environ, {"GITLAB_URL": "https://env.gitlab.com"}):
            file_config = {"gitlab": {"url": "https://file.gitlab.com"}}
            result = config.get_gitlab_url(file_config)

            assert result == "https://file.gitlab.com"

    def test_env_var_overrides_default(self):
        """Environment variables should override defaults."""
        with patch.dict(os.environ, {"GITLAB_URL": "https://env.gitlab.com"}):
            result = config.get_gitlab_url({})

            assert result == "https://env.gitlab.com"

    def test_default_when_no_config_no_env(self):
        """Default value when no config file and no env var."""
        with patch.dict(os.environ, {}, clear=True):
            result = config.get_gitlab_url({})

            assert result == config.DEFAULT_GITLAB_URL


class TestGetGitlabUrl:
    """Tests for get_gitlab_url function."""

    def test_get_gitlab_url_default(self):
        """Test default GitLab URL."""
        with patch.dict(os.environ, {}, clear=True):
            result = config.get_gitlab_url({})

            assert result == config.DEFAULT_GITLAB_URL

    def test_get_gitlab_url_from_env(self):
        """Test GitLab URL from environment."""
        with patch.dict(os.environ, {"GITLAB_URL": "https://env.gitlab.com"}):
            result = config.get_gitlab_url({})

            assert result == "https://env.gitlab.com"

    def test_get_gitlab_url_from_file(self):
        """Test GitLab URL from config file."""
        with patch.dict(os.environ, {}, clear=True):
            file_config = {"gitlab": {"url": "https://file.gitlab.com"}}

            result = config.get_gitlab_url(file_config)

            assert result == "https://file.gitlab.com"


class TestGetGitlabToken:
    """Tests for get_gitlab_token function."""

    def test_get_gitlab_token_default(self):
        """Test default GitLab token."""
        with patch.dict(os.environ, {}, clear=True):
            result = config.get_gitlab_token({})

            assert result == "changeme"

    def test_get_gitlab_token_from_env(self):
        """Test GitLab token from environment."""
        with patch.dict(os.environ, {"GITLAB_TOKEN": "env_token"}):
            result = config.get_gitlab_token({})

            assert result == "env_token"


class TestGetConfluenceUrl:
    """Tests for get_confluence_url function."""

    def test_get_confluence_url_default(self):
        """Test default Confluence URL."""
        with patch.dict(os.environ, {}, clear=True):
            result = config.get_confluence_url({})

            assert result == config.DEFAULT_CONFLUENCE_URL

    def test_get_confluence_url_from_env(self):
        """Test Confluence URL from environment."""
        with patch.dict(os.environ, {"CONFLUENCE_URL": "https://env.confluence.com"}):
            result = config.get_confluence_url({})

            assert result == "https://env.confluence.com"


class TestGetHistoryCount:
    """Tests for get_history_count function."""

    def test_get_history_count_default(self):
        """Test default history count."""
        with patch.dict(os.environ, {}, clear=True):
            result = config.get_history_count({})

            assert result == 10

    def test_get_history_count_from_env(self):
        """Test history count from environment."""
        with patch.dict(os.environ, {"HISTORY_COUNT": "25"}):
            result = config.get_history_count({})

            assert result == 25

    def test_get_history_count_from_file(self):
        """Test history count from config file."""
        with patch.dict(os.environ, {}, clear=True):
            file_config = {"options": {"history_count": 15}}

            result = config.get_history_count(file_config)

            assert result == 15

    def test_get_history_count_invalid(self):
        """Test history count with invalid value."""
        with patch.dict(os.environ, {"HISTORY_COUNT": "invalid"}):
            result = config.get_history_count({})

            assert result == 10


class TestGetConfluenceEmail:
    """Tests for get_confluence_email function."""

    def test_get_confluence_email_default(self):
        """Test default Confluence email."""
        with patch.dict(os.environ, {}, clear=True):
            result = config.get_confluence_email({})

            assert result == "changeme"

    def test_get_confluence_email_from_env(self):
        """Test Confluence email from environment."""
        with patch.dict(os.environ, {"CONFLUENCE_EMAIL": "test@example.com"}):
            result = config.get_confluence_email({})

            assert result == "test@example.com"


class TestGetConfluenceToken:
    """Tests for get_confluence_token function."""

    def test_get_confluence_token_default(self):
        """Test default Confluence token."""
        with patch.dict(os.environ, {}, clear=True):
            result = config.get_confluence_token({})

            assert result == "changeme"

    def test_get_confluence_token_from_env(self):
        """Test Confluence token from environment."""
        with patch.dict(os.environ, {"CONFLUENCE_TOKEN": "conf_token"}):
            result = config.get_confluence_token({})

            assert result == "conf_token"


class TestValidateConfigKeys:
    """Tests for validate_config_keys function."""

    def test_validate_config_keys_no_warning_valid(self):
        """No warning for valid keys."""
        import warnings as warnings_module
        with warnings_module.catch_warnings(record=True) as record:
            warnings_module.simplefilter("always")
            config.validate_config_keys(
                {"gitlab": {"url": "https://gitlab.com", "token": "secret"}},
                {"gitlab": ["url", "token"]},
            )

        assert len(record) == 0

    def test_validate_config_keys_warns_unknown(self):
        """Warning for unknown keys."""
        with pytest.warns(UserWarning, match="Unknown key"):
            config.validate_config_keys(
                {"gitlab": {"url": "https://gitlab.com", "server_url": "wrong"}},
                {"gitlab": ["url", "token"]},
            )

    def test_validate_config_keys_missing_section(self):
        """No warning when section is missing."""
        import warnings as warnings_module
        with warnings_module.catch_warnings(record=True) as record:
            warnings_module.simplefilter("always")
            config.validate_config_keys(
                {"other": {"url": "https://example.com"}},
                {"gitlab": ["url", "token"]},
            )

        assert len(record) == 0

    def test_validate_config_keys_multiple_unknown(self):
        """Warning for multiple unknown keys."""
        with pytest.warns(UserWarning, match="server_url.*typo"):
            config.validate_config_keys(
                {
                    "gitlab": {
                        "url": "https://gitlab.com",
                        "server_url": "wrong1",
                        "token_secret": "wrong2",
                    }
                },
                {"gitlab": ["url", "token"]},
            )
