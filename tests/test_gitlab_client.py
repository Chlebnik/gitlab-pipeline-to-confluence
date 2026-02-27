"""Unit tests for GitLab client module."""

import pytest
from unittest.mock import MagicMock, patch

from gitlab_client import GitLabClient


class TestGitLabClient:
    """Tests for GitLabClient class."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock requests session."""
        with patch("gitlab_client.requests.Session") as mock:
            session = MagicMock()
            mock.return_value = session
            yield session

    @pytest.fixture
    def client(self, mock_session):
        """Create GitLabClient with mocked session."""
        return GitLabClient(
            url="https://gitlab.example.com",
            token="test_token"
        )

    def test_init_with_custom_url_and_token(self, mock_session):
        """Test initialization with custom URL and token."""
        client = GitLabClient(
            url="https://custom.gitlab.com",
            token="my_token"
        )

        assert client.url == "https://custom.gitlab.com"
        assert client.token == "my_token"

    def test_init_with_defaults(self, mock_session):
        """Test initialization with default values."""
        with patch("gitlab_client.config") as mock_config:
            mock_config.GITLAB_URL = "https://default.gitlab.com"
            mock_config.GITLAB_TOKEN = "default_token"

            client = GitLabClient()

            assert client.url == "https://default.gitlab.com"
            assert client.token == "default_token"

    def test_get_pipeline(self, client, mock_session):
        """Test getting a pipeline."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 123,
            "name": "main",
            "status": "success",
        }
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response

        result = client.get_pipeline("project1", 123)

        assert result["id"] == 123
        assert result["name"] == "main"
        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert "123" in call_args[0][0]

    def test_get_pipeline_test_report_summary(self, client, mock_session):
        """Test getting pipeline test report summary."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "total": {
                "count": 100,
                "success": 95,
                "failed": 5,
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response

        result = client.get_pipeline_test_report_summary("project1", 123)

        assert result["total"]["count"] == 100
        assert result["total"]["success"] == 95

    def test_get_pipelines_default(self, client, mock_session):
        """Test getting pipelines with default parameters."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": 1, "status": "success"},
            {"id": 2, "status": "failed"},
        ]
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response

        result = client.get_pipelines("project1")

        assert len(result) == 2
        assert result[0]["id"] == 1

    def test_get_pipelines_with_status_filter(self, client, mock_session):
        """Test getting pipelines with status filter."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": 1, "status": "success"}]
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response

        result = client.get_pipelines("project1", status="success")

        assert len(result) == 1
        call_args = mock_session.get.call_args
        assert "status" in call_args[1].get("params", {})

    def test_get_pipelines_with_per_page(self, client, mock_session):
        """Test getting pipelines with custom per_page."""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response

        client.get_pipelines("project1", per_page=50)

        call_args = mock_session.get.call_args
        assert call_args[1]["params"]["per_page"] == 50
