"""Integration tests for Confluence API flow."""

import pytest
import responses

from confluence_client import ConfluenceClient
from generator import find_and_replace_section


# Confluence API Response Examples from documentation

CONFLUENCE_GET_PAGE_RESPONSE = {
    "id": "123456",
    "type": "page",
    "status": "current",
    "title": "Pipeline Results",
    "body": {
        "storage": {
            "value": "<h2>my-app</h2><p>Old content here</p><h2>other-app</h2><p>More content</p>",
            "representation": "storage"
        }
    },
    "version": {
        "number": 5,
        "message": "Previous update"
    }
}

CONFLUENCE_UPDATE_PAGE_RESPONSE = {
    "id": "123456",
    "type": "page",
    "status": "current",
    "title": "Pipeline Results",
    "body": {
        "storage": {
            "value": "<h2>my-app</h2><p>New content</p>",
            "representation": "storage"
        }
    },
    "version": {
        "number": 6,
        "message": "Updated via GitLab pipeline script"
    }
}


class TestConfluenceResponses:
    """Test parsing Confluence API responses."""

    def test_get_page_returns_content(self):
        """Test getting page returns correct content structure."""
        response = CONFLUENCE_GET_PAGE_RESPONSE

        assert response["id"] == "123456"
        assert response["type"] == "page"
        assert response["title"] == "Pipeline Results"
        assert response["body"]["storage"]["representation"] == "storage"
        assert "<h2>my-app</h2>" in response["body"]["storage"]["value"]
        assert response["version"]["number"] == 5

    def test_update_page_structure(self):
        """Test update page request structure."""
        request_body = {
            "id": "123456",
            "type": "page",
            "title": "Pipeline Results",
            "body": {
                "storage": {
                    "value": "<h2>my-app</h2><p>New content</p>",
                    "representation": "storage"
                }
            },
            "version": {
                "number": 6,
                "message": "Updated via GitLab pipeline script"
            }
        }

        assert request_body["id"] == "123456"
        assert request_body["version"]["number"] == 6
        assert request_body["body"]["storage"]["representation"] == "storage"


class TestFindAndReplaceSection:
    """Test section replacement in Confluence content."""

    def test_find_and_replace_existing_section(self):
        """Test replacing existing section in page content."""
        content = "<h2>my-app</h2><p>Old content</p><h2>other-app</h2><p>More</p>"
        new_section = "<h2>my-app</h2><p>New content</p>"

        result = find_and_replace_section(content, "my-app", new_section)

        assert "New content" in result
        assert "<p>Old content</p>" not in result

    def test_append_when_section_not_found(self):
        """Test appending section when not found."""
        content = "<h2>other-app</h2><p>Content</p>"
        new_section = "<h2>my-app</h2><p>New</p>"

        result = find_and_replace_section(content, "my-app", new_section)

        assert result.endswith(new_section)

    def test_case_insensitive_match(self):
        """Test case insensitive matching for section names."""
        content = "<h2>My-App</h2><p>Old</p>"
        new_section = "<h2>My-App</h2><p>New</p>"

        result = find_and_replace_section(content, "my-app", new_section)

        assert "New" in result


@responses.activate
class TestConfluenceAPIMocking:
    """Integration tests with mocked Confluence API responses."""

    def test_get_page_from_api(self):
        """Test fetching page from mocked Confluence API."""
        responses.add(
            responses.GET,
            "https://confluence.example.com/rest/api/content/123456",
            json=CONFLUENCE_GET_PAGE_RESPONSE,
            status=200,
            params={"expand": "body.storage,version"},
        )

        client = ConfluenceClient(
            url="https://confluence.example.com",
            email="test@example.com",
            token="test_token"
        )
        result = client.get_page("123456")

        assert result["id"] == "123456"
        assert result["title"] == "Pipeline Results"
        assert result["version"]["number"] == 5

    def test_update_page_to_api(self):
        """Test updating page with mocked Confluence API."""
        responses.add(
            responses.PUT,
            "https://confluence.example.com/rest/api/content/123456",
            json=CONFLUENCE_UPDATE_PAGE_RESPONSE,
            status=200,
        )

        client = ConfluenceClient(
            url="https://confluence.example.com",
            email="test@example.com",
            token="test_token"
        )

        result = client.update_page(
            "123456",
            "Pipeline Results",
            "<h2>my-app</h2><p>New content</p>",
            5
        )

        assert result["version"]["number"] == 6

    def test_full_confluence_flow(self):
        """Test complete Confluence flow with mocked API."""
        # Mock get page
        responses.add(
            responses.GET,
            "https://confluence.example.com/rest/api/content/123456",
            json=CONFLUENCE_GET_PAGE_RESPONSE,
            status=200,
        )

        # Mock update page
        responses.add(
            responses.PUT,
            "https://confluence.example.com/rest/api/content/123456",
            json=CONFLUENCE_UPDATE_PAGE_RESPONSE,
            status=200,
        )

        client = ConfluenceClient(
            url="https://confluence.example.com",
            email="test@example.com",
            token="test_token"
        )

        # Get page
        page = client.get_page("123456")
        current_content = page["body"]["storage"]["value"]
        current_version = page["version"]["number"]

        # Generate new section
        new_section = "<h2>my-app</h2><p>Updated with latest pipeline results</p>"
        new_content = find_and_replace_section(current_content, "my-app", new_section)

        # Update page
        updated = client.update_page(
            "123456",
            page["title"],
            new_content,
            current_version
        )

        assert updated["version"]["number"] == current_version + 1
        assert "Updated with latest pipeline results" in new_content
