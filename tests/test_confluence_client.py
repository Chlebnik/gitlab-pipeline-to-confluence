"""Unit tests for Confluence client module."""

import pytest
from unittest.mock import MagicMock, patch

from confluence_client import ConfluenceClient


class TestConfluenceClient:
    """Tests for ConfluenceClient class."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock requests session."""
        with patch("confluence_client.requests.Session") as mock:
            session = MagicMock()
            mock.return_value = session
            yield session

    @pytest.fixture
    def client(self, mock_session):
        """Create ConfluenceClient with mocked session."""
        return ConfluenceClient(
            url="https://confluence.example.com",
            email="test@example.com",
            token="test_token"
        )

    def test_init_with_custom_values(self, mock_session):
        """Test initialization with custom values."""
        client = ConfluenceClient(
            url="https://custom.confluence.com",
            email="user@company.com",
            token="my_token"
        )

        assert client.url == "https://custom.confluence.com"
        assert client.email == "user@company.com"
        assert client.token == "my_token"

    def test_init_with_defaults(self, mock_session):
        """Test initialization with default values."""
        with patch("confluence_client.config") as mock_config:
            mock_config.CONFLUENCE_URL = "https://default.confluence.com"
            mock_config.CONFLUENCE_EMAIL = "default@example.com"
            mock_config.CONFLUENCE_TOKEN = "default_token"

            client = ConfluenceClient()

            assert client.url == "https://default.confluence.com"
            assert client.email == "default@example.com"
            assert client.token == "default_token"

    def test_get_page(self, client, mock_session):
        """Test getting a Confluence page."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "12345",
            "title": "Test Page",
            "body": {"storage": {"value": "<p>Content</p>"}},
            "version": {"number": 3},
        }
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response

        result = client.get_page("12345")

        assert result["id"] == "12345"
        assert result["title"] == "Test Page"
        assert result["body"]["storage"]["value"] == "<p>Content</p>"
        assert result["version"]["number"] == 3

    def test_get_page_expand_params(self, client, mock_session):
        """Test that get_page uses correct expand params."""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response

        client.get_page("12345")

        call_args = mock_session.get.call_args
        assert "params" in call_args[1]
        assert "expand" in call_args[1]["params"]
        assert "body.storage" in call_args[1]["params"]["expand"]
        assert "version" in call_args[1]["params"]["expand"]

    def test_update_page(self, client, mock_session):
        """Test updating a Confluence page."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "12345",
            "title": "Test Page",
            "version": {"number": 4},
        }
        mock_response.raise_for_status = MagicMock()
        mock_session.put.return_value = mock_response

        result = client.update_page(
            "12345",
            "Test Page",
            "<p>Updated content</p>",
            3
        )

        assert result["version"]["number"] == 4

        call_args = mock_session.put.call_args
        request_data = call_args[1]["json"]

        assert request_data["id"] == "12345"
        assert request_data["type"] == "page"
        assert request_data["title"] == "Test Page"
        assert request_data["version"]["number"] == 4
        assert request_data["version"]["message"] == "Updated via GitLab pipeline script"

    def test_update_page_increments_version(self, client, mock_session):
        """Test that update_page increments version number."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"version": {"number": 5}}
        mock_response.raise_for_status = MagicMock()
        mock_session.put.return_value = mock_response

        client.update_page("12345", "Title", "Content", 4)

        call_args = mock_session.put.call_args
        request_data = call_args[1]["json"]

        assert request_data["version"]["number"] == 5

    def test_update_page_uses_storage_representation(self, client, mock_session):
        """Test that update_page uses storage representation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()
        mock_session.put.return_value = mock_response

        client.update_page("12345", "Title", "<p>HTML Content</p>", 1)

        call_args = mock_session.put.call_args
        request_data = call_args[1]["json"]

        assert request_data["body"]["storage"]["representation"] == "storage"
        assert request_data["body"]["storage"]["value"] == "<p>HTML Content</p>"
